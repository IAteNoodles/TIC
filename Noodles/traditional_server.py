from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from rich.logging import RichHandler
import os
import json
import base64
from datetime import date, datetime, time
from dotenv import load_dotenv
import httpx
from neo4j import GraphDatabase
from neo4j.time import Date, DateTime, Time, Duration
from pydantic import BaseModel

# Assuming these are defined elsewhere or add placeholders

class CypherQueryRequest(BaseModel):
    cypher_query: str



app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust origins as needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
    handlers=[RichHandler()]
)

logger = logging.getLogger("noodles")
logger.debug("Verbose logging enabled with color and timestamps.")


load_dotenv()

AURA_USER = os.getenv("AURA_USER")
AURA_PASSWORD = os.getenv("AURA_PASSWORD")
URI = "neo4j://98d1982d.databases.neo4j.io"
AUTH = (AURA_USER, AURA_PASSWORD)
# Custom JSON encoder for Neo4j types
class Neo4jJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if obj is None:
            return None
        elif isinstance(obj, (Date, DateTime)):
            return obj.isoformat()
        elif isinstance(obj, Time):
            return obj.isoformat()
        elif isinstance(obj, Duration):
            return str(obj)
        elif isinstance(obj, (date, datetime, time)):
            return obj.isoformat()
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        elif hasattr(obj, '__str__'):
            return str(obj)
        return super().default(obj)

def serialize_neo4j_result(result):
    """Convert Neo4j result to JSON-serializable format"""
    def convert_value(value):
        if value is None:
            return None
        elif isinstance(value, (Date, DateTime, Time, Duration, date, datetime, time)):
            return str(value)
        elif hasattr(value, 'isoformat'):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: convert_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [convert_value(v) for v in value]
        elif hasattr(value, '__str__'):
            return str(value)
        return value
    
    if isinstance(result, dict):
        return {k: convert_value(v) for k, v in result.items()}
    elif isinstance(result, list):
        return [convert_value(item) for item in result]
    return convert_value(result)


# -----------------------
# Mistral OCR utilities
# -----------------------

def _mask_key(key: str) -> str:
    if not key:
        return "<empty>"
    k = key.strip()
    if len(k) <= 8:
        return "*" * len(k)
    return f"{k[:4]}***{k[-4:]} (len={len(k)})"


def get_mistral_client():
    try:
        from mistralai import Mistral  # imported lazily to avoid hard dep at startup
    except Exception as e:
        logger.error("mistralai package not installed. Run: pip install mistralai")
        raise HTTPException(status_code=500, detail="mistralai package not installed")

    raw_key = os.environ.get("MISTRAL_API_KEY", "")
    api_key = raw_key.strip().strip('"').strip("'")
    if not api_key:
        logger.error("MISTRAL_API_KEY missing")
        raise HTTPException(status_code=500, detail="MISTRAL_API_KEY not configured in environment")

    logger.info(f"Mistral API key loaded (masked): {_mask_key(api_key)}")
    client = Mistral(api_key=api_key)

    # Validate key by hitting models endpoint
    try:
        client.models.list()
    except Exception as auth_error:
        logger.error(f"Mistral API authentication failed: {auth_error}")
        raise HTTPException(status_code=401, detail="Invalid MISTRAL_API_KEY. Check and update your .env")
    return client


@app.get("/ocr/health")
async def ocr_health():
    """Quick check that Mistral API key is valid and reachable."""
    client = get_mistral_client()
    try:
        models = client.models.list()
        return {"ok": True, "models": [getattr(m, "id", None) or getattr(m, "name", None) for m in getattr(models, "data", [])]}
    except Exception as e:
        logger.error(f"OCR health check failed: {e}")
        raise HTTPException(status_code=502, detail=str(e))

# --- OCR Helper Function --------------------------------------------------

def _extract_text_from_ocr_response(ocr_response) -> str:
    """Normalize different possible OCR response shapes to plain text.
    Supports SDK pydantic model objects or raw dict replies.
    """
    if ocr_response is None:
        return ""
    # If pydantic model, prefer model_dump() if available
    if hasattr(ocr_response, "model_dump"):
        try:
            data = ocr_response.model_dump()
        except Exception:
            data = None
    else:
        data = None

    pages = []
    # Priority: direct attribute .pages
    if hasattr(ocr_response, "pages") and ocr_response.pages is not None:
        pages = ocr_response.pages
    elif isinstance(data, dict) and isinstance(data.get("pages"), list):
        pages = data.get("pages")
    elif isinstance(ocr_response, dict) and isinstance(ocr_response.get("pages"), list):
        pages = ocr_response.get("pages")

    segments = []
    for p in pages:
        if p is None:
            continue
        if isinstance(p, dict):
            seg = p.get("markdown") or p.get("text") or ""
        else:  # object with attributes
            seg = getattr(p, "markdown", None) or getattr(p, "text", "")
        if seg:
            segments.append(seg.strip())
    return "\n\n".join(segments)

# --- Health Check ---
@app.get("/health")
async def health_check():
    """
    Health check endpoint for backend service and database connectivity.
    
    Args:
        db (pymysql.Connection): Database connection dependency.
        
    Returns:
        dict: Health status containing:
            - status (str): Overall service status ('ok' or 'error')
            - database (str): Database connectivity status
            
    Raises:
        HTTPException: If health check fails (status 500).
    """
    """Backend health and connectivity check."""
    logger.info("Performing health check.")
    try:
        driver = get_neo4j_driver()
        verify_neo4j_connection(driver)
        driver.close()
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

def get_neo4j_driver():
    """Create and return a Neo4j driver with proper configuration for Aura"""
    uri = URI
    user = AURA_USER
    password = AURA_PASSWORD
    
    if not all([uri, user, password]):
        raise HTTPException(status_code=500, detail="Missing Neo4j credentials")
    
    # Configuration for Neo4j Aura
    driver_config = {
        "encrypted": True,
        "trust": 'TRUST_ALL_CERTIFICATES'  # TRUST_ALL_CERTIFICATES
    }
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password), **driver_config)
        logger.info(f"Neo4j driver created for URI: {uri}")
        return driver
    except Exception as e:
        logger.error(f"Failed to create Neo4j driver: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create Neo4j driver: {str(e)}")

def verify_neo4j_connection(driver):
    """Verify Neo4j connection using modern driver API"""
    try:
        driver.verify_connectivity()
        logger.info("Neo4j connectivity verified successfully")
        return True
    except Exception as e:
        logger.error(f"Neo4j connectivity failed: {str(e)}")
        raise

@app.post("/run_cypher_query")
async def run_cypher_query(request: CypherQueryRequest):
    """
    Execute a Cypher query on the Neo4j database with improved error handling.
    
    Args:
        request (CypherQueryRequest): JSON request containing:
            - cypher_query (str): The Cypher query to execute.
        
    Returns:
        dict: The result of the query or an error message.
    """
    logger.info(f"Executing Cypher query: {request.cypher_query}")
    
    # Log connection details (without password)
    logger.info(f"Neo4j URI: {URI}")
    logger.info(f"Neo4j User: {AURA_USER}")
    logger.info("Neo4j Password is set." if AURA_PASSWORD else "Neo4j Password is NOT set.")
    
    driver = None
    try:
        # Create driver with improved configuration
        driver = get_neo4j_driver()
        
        # Verify connectivity with retry logic
        verify_neo4j_connection(driver)
        
        # Execute the query using modern driver API
        logger.info("Executing Cypher query")
        result = driver.execute_query(request.cypher_query)
        
        logger.info(f"Query executed successfully. Retrieved {len(result.records)} records")
        
        # Convert records to dict format
        records = [dict(record) for record in result.records]
        
        # Apply serialization to handle Neo4j temporal types
        serialized_records = serialize_neo4j_result(records)
        
        return {"status": "success", "results": serialized_records, "count": len(serialized_records)}
            
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    
    except Exception as e:
        error_msg = f"Error executing Cypher query: {str(e)}"
        logger.error(error_msg)
        return {"status": "error", "error": error_msg}
    
    finally:
        # Ensure driver is properly closed
        if driver:
            try:
                driver.close()
                logger.info("Neo4j driver closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j driver: {str(e)}")


# --- OCR Endpoints -------------------------------------------------------

@app.post("/extract-image")
async def extract_data_from_image(file: UploadFile = File(...)):
    """
    Extract data from an uploaded image using OCR and return extracted text.
    """
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        client = get_mistral_client()

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}"
            },
            include_image_base64=False
        )
        text = _extract_text_from_ocr_response(ocr_response)
        logger.info(f"Successfully extracted text from image: {len(text)} characters")
        return {"text": text}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error extracting text from image: {error_msg}")
        if "401" in error_msg or "Unauthorized" in error_msg:
            return JSONResponse(status_code=401, content={"error": "MISTRAL_API_KEY is invalid or expired. Please update it in your .env file."})
        return JSONResponse(status_code=500, content={"error": error_msg})


# --- Improved OCR Endpoints with Better Error Handling ---

@app.post("/extract-image-improved")
async def extract_data_from_image_improved(file: UploadFile = File(...)):
    """
    Extract data from an uploaded image using OCR and return extracted text.
    """
    try:
        contents = await file.read()
        base64_image = base64.b64encode(contents).decode('utf-8')
        client = get_mistral_client()

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": f"data:image/jpeg;base64,{base64_image}"
            },
            include_image_base64=False
        )
        text = _extract_text_from_ocr_response(ocr_response)
        logger.info(f"Successfully extracted text from image: {len(text)} characters")
        return {"text": text}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error extracting text from image: {error_msg}")
        if "401" in error_msg or "Unauthorized" in error_msg:
            return JSONResponse(status_code=401, content={"error": "MISTRAL_API_KEY is invalid or expired. Please update it in your .env file."})
        return JSONResponse(status_code=500, content={"error": error_msg})


@app.post("/extract-pdf")
async def extract_data_from_pdf(file: UploadFile = File(...)):
    """
    Extract data from an uploaded PDF using OCR and return extracted text.
    """
    try:
        contents = await file.read()
        base64_pdf = base64.b64encode(contents).decode('utf-8')
        client = get_mistral_client()
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            include_image_base64=False
        )
        text = _extract_text_from_ocr_response(ocr_response)
        logger.info(f"Successfully extracted text from PDF: {len(text)} characters")
        return {"text": text}
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return JSONResponse(status_code=500, content={"error": str(e)})


# --- Improved OCR Endpoints with Better Error Handling ---

@app.post("/extract-pdf-improved")
async def extract_data_from_pdf_improved(file: UploadFile = File(...)):
    """
    Extract data from an uploaded PDF using OCR and return extracted text.
    """
    try:
        contents = await file.read()
        base64_pdf = base64.b64encode(contents).decode('utf-8')
        client = get_mistral_client()

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}"
            },
            include_image_base64=False
        )
        text = _extract_text_from_ocr_response(ocr_response)
        logger.info(f"Successfully extracted text from PDF: {len(text)} characters")
        return {"text": text}
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error extracting text from PDF: {error_msg}")
        if "401" in error_msg or "Unauthorized" in error_msg:
            return JSONResponse(status_code=401, content={"error": "MISTRAL_API_KEY is invalid or expired. Please update it in your .env file."})
        return JSONResponse(status_code=500, content={"error": error_msg})



@app.get("/get_patient_complete_details")
async def get_patients_complete_details(patient_id: str = None):
    """
    Fetch complete patient details from the Neo4j database.
    
    Args:
        patient_id (str, optional): Specific patient ID to filter results. If None, fetch

    Returns:
        dict: Patient details or an error message.
    
    """
    logger.info("Fetching complete patient details")
    driver = None
    try:
        driver = get_neo4j_driver()
        verify_neo4j_connection(driver)

        # Fetch personal details
        if patient_id:
            personal_query = """
            MATCH (p:Patient {{patient_id: {patient_id}}})
            RETURN p
            """.format(patient_id=patient_id)
            personal_result = driver.execute_query(personal_query)
        else:
            personal_query = """
            MATCH (p:Patient)
            RETURN p
            LIMIT 100
            """
            personal_result = driver.execute_query(personal_query)
        
        personal_records = [dict(record) for record in personal_result.records]
        
        # Fetch lab details
        if patient_id:
            lab_query = """
            MATCH (p:Patient {{patient_id: {patient_id}}})-[:HAS_HEALTH_VALUES]->(hv:LabValues)
            RETURN hv
            """.format(patient_id=patient_id)
            lab_result = driver.execute_query(lab_query)
        else:
            lab_query = """
            MATCH (p:Patient)-[:HAS_HEALTH_VALUES]->(hv:LabValues)
            RETURN hv
            """
            lab_result = driver.execute_query(lab_query)
        
        lab_records = [dict(record) for record in lab_result.records]
        
        # Combine personal and lab details
        combined_results = []
        for personal in personal_records:
            # Get the patient node from the record
            patient_node = personal.get('p')
            if patient_node is None:
                # If 'p' key doesn't exist, try to get the first value
                patient_node = list(personal.values())[0] if personal else None
            
            # Serialize personal details properly
            if patient_node:
                try:
                    personal_props = dict(patient_node)
                except:
                    personal_props = getattr(patient_node, "properties", None) or getattr(patient_node, "_properties", None) or {}
            else:
                personal_props = {}
            
            patient_data = {
                "personal_details": serialize_neo4j_result(personal_props),
                "lab_details": []
            }
            
            # Add lab details for this patient
            for lab in lab_records:
                lab_node = lab.get('hv')
                if lab_node:
                    try:
                        lab_props = dict(lab_node)
                    except:
                        lab_props = getattr(lab_node, "properties", None) or getattr(lab_node, "_properties", None) or {}
                    patient_data["lab_details"].append(serialize_neo4j_result(lab_props))
            
            combined_results.append(patient_data)
        
        logger.info(f"Fetched {len(combined_results)} patient records with personal and lab details")
        return {"status": "success", "patients": combined_results, "count": len(combined_results)}
    
    except HTTPException:
        raise
    
    except Exception as e:
        error_msg = f"Error fetching patient details: {str(e)}"
        logger.error(error_msg)
        return JSONResponse(status_code=500, content={"error": error_msg})
    
    finally:
        if driver:
            try:
                driver.close()
                logger.info("Neo4j driver closed")
            except Exception as e:
                logger.warning(f"Error closing Neo4j driver: {str(e)}")



if __name__ == "__main__":
    import uvicorn
    import socket
    # Get the local network IP address
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Server running at http://0.0.0.0:8001 (accessible from your network at http://{local_ip}:8001)")
    uvicorn.run("traditional_server:app", host="0.0.0.0", port=8001, reload=True)
