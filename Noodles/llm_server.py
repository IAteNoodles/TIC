from fastmcp import FastMCP
import socket
import requests
import time
from typing import Dict, Any

mcp = FastMCP("CDSX")
def _to_int(val: Any, default: int | None = None) -> int:
    try:
        return int(str(val).strip())
    except Exception:
        if default is not None:
            return default
        raise ValueError(f"Expected integer, got {val!r}")


def _to_float(val: Any, default: float | None = None) -> float:
    try:
        return float(str(val).strip())
    except Exception:
        if default is not None:
            return default
        raise ValueError(f"Expected float, got {val!r}")


def _to_flag(val: Any, default: int | None = None) -> int:
    s = str(val).strip().lower()
    truthy = {"1", "true", "yes", "y", "on"}
    falsy = {"0", "false", "no", "n", "off"}
    if s in truthy:
        return 1
    if s in falsy:
        return 0
    try:
        i = int(s)
        if i in (0, 1):
            return i
    except Exception:
        pass
    if default is not None:
        return default
    raise ValueError(f"Expected 0/1 boolean-like value, got {val!r}")


def _normalize_gender(val: Any) -> int:
    s = str(val).strip().lower()
    if s in ("male", "m", "1"):
        return 1
    if s in ("female", "f", "0"):
        return 0
    # try numeric
    try:
        i = int(s)
        if i in (0, 1):
            return i
    except Exception:
        pass
    raise ValueError("gender must be one of: 'Male','Female','M','F','1','0'")


def _normalize_smoking_history(val: Any) -> str:
    # Allow variety but return a canonical lowercase token
    s = str(val).strip().lower()
    aliases = {
        "never": {"never", "no", "none", "n"},
        "current": {"current", "yes", "y", "now"},
        "former": {"former", "past", "quit", "ex"},
        "ever": {"ever"},
        "not current": {"not current", "not_current"},
    }
    for canon, aset in aliases.items():
        if s in aset:
            return canon
    return s  # fallback to provided token


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 30) -> Dict[str, Any]:
    """Post JSON payload to a URL and return response plus timing.

    Sends a JSON POST request to the provided `url` with the given
    `payload` and measures the elapsed time for the request in
    milliseconds. The function attempts to decode the response body as
    JSON; if decoding fails the raw text is returned under the key
    ``raw_text``.

    Args:
        url (str): The full URL to POST the JSON payload to.
        payload (Dict[str, Any]): The JSON-serializable payload to send
            in the POST body.
        timeout (int): Request timeout in seconds. Defaults to 30.

    Returns:
        Dict[str, Any]: A dictionary with the keys:
            - ``status_code`` (int): HTTP response code returned by server.
            - ``body`` (dict): Decoded JSON response or ``{"raw_text": ...}``.
            - ``elapsed_ms`` (float): Time taken for the request in ms.

    Raises:
        requests.exceptions.RequestException: Propagates network-related
            exceptions raised by the underlying ``requests`` call.
    """
    start = time.time()
    resp = requests.post(url, json=payload, timeout=timeout)
    elapsed_ms = (time.time() - start) * 1000
    try:
        body = resp.json()
    except Exception:
        body = {"raw_text": resp.text}
    return {"status_code": resp.status_code, "body": body, "elapsed_ms": elapsed_ms}


@mcp.tool("call_cardio_api")
def call_cardio_api(
    age: float,
    gender: str,
    height: float,
    weight: float,
    ap_hi: float,
    ap_lo: float,
    cholesterol: float,
    gluc: float,
    smoke: int,
    alco: int,
    active: int,
) -> Dict[str, Any]:
    """Call the cardiovascular prediction API with explicit arguments.

    Accepts each expected cardiovascular input separately. Builds the
    payload and posts to ``http://localhost:5002/predict``. The underlying
    API expects ``gender`` as 0 (female) or 1 (male), but this tool accepts
    a human-friendly string and coerces it.

    Args:
        age (float): Age in years.
        gender (str): Gender string. Accepted values (case-insensitive):
            - "Male", "M", "1" -> 1
            - "Female", "F", "0" -> 0
            Also accepts numeric strings like "0"/"1".
        height (float): Height in cm.
        weight (float): Weight in kg.
        ap_hi (float): Systolic blood pressure (mmHg).
        ap_lo (float): Diastolic blood pressure (mmHg).
        cholesterol (float): Cholesterol category 1/2/3.
        gluc (float): Glucose category 1/2/3.
        smoke (int): Smoking flag 0/1.
        alco (int): Alcohol flag 0/1.
        active (int): Physical activity 0/1.

    Returns:
        Dict[str, Any]: Minimal response with ``prediction`` and optional
        ``explanations`` if provided by the service.

    Raises:
        ValueError: If ``gender`` cannot be coerced to 0/1.
        requests.exceptions.RequestException: If the POST fails.
    """
    # Coerce inputs permissively
    # Convert external floats to backend-required ints
    age_i = int(_to_float(age))
    gender_int = _normalize_gender(gender)
    height_i = int(_to_float(height))
    weight_i = int(_to_float(weight))
    ap_hi_i = int(_to_float(ap_hi))
    ap_lo_i = int(_to_float(ap_lo))
    cholesterol_i = int(_to_float(cholesterol))
    gluc_i = int(_to_float(gluc))
    smoke_i = _to_flag(smoke)
    alco_i = _to_flag(alco)
    active_i = _to_flag(active)
    url = "http://localhost:5002/predict"
    payload = {
        "age": age_i,
        "gender": gender_int,
        "height": height_i,
        "weight": weight_i,
        "ap_hi": ap_hi_i,
        "ap_lo": ap_lo_i,
        "cholesterol": cholesterol_i,
        "gluc": gluc_i,
        "smoke": smoke_i,
        "alco": alco_i,
        "active": active_i,
    }
    result = _post_json(url, payload)
    # Extract only prediction and explanations to avoid leaking internals
    body = result.get("body", {}) if isinstance(result, dict) else {}
    minimal = {}
    if isinstance(body, dict) and "prediction" in body:
        minimal["prediction"] = body.get("prediction")
    if isinstance(body, dict) and "explanations" in body:
        minimal["explanations"] = body.get("explanations")
    return minimal


@mcp.tool("call_diabetes_api")
def call_diabetes_api(
    age: float,
    gender: str,
    hypertension: int,
    heart_disease: int,
    smoking_history: str,
    bmi: float,
    HbA1c_level: float,
    blood_glucose_level: float,
) -> Dict[str, Any]:
    """Call the diabetes model prediction endpoint using explicit args.

    Accepts each expected diabetes input as a separate argument. The
    function constructs the payload internally and posts to
    ``http://localhost:5003/predict`` returning the response plus timing.

    Args:
    age (float): Age in years.
        gender (str): Gender string (e.g., "Male", "Female", "Other").
    hypertension (int): Hypertension flag 0/1.
    heart_disease (int): Heart disease flag 0/1.
        smoking_history (str): Smoking history descriptor (canonicalized to lowercase token like "never", "current", "former", "ever").
        bmi (float): Body Mass Index.
        HbA1c_level (float): HbA1c percentage.
        blood_glucose_level (float): Blood glucose in mg/dL.

    Returns:
        Dict[str, Any]: Result dictionary returned by ``_post_json``.

    Raises:
        requests.exceptions.RequestException: If the POST fails.
    """
    url = "http://localhost:5003/predict"
    payload = {
        "age": _to_float(age),
        "gender": gender,
        "hypertension": _to_flag(hypertension),
        "heart_disease": _to_flag(heart_disease),
        "smoking_history": _normalize_smoking_history(smoking_history),
        "bmi": _to_float(bmi),
        "HbA1c_level": _to_float(HbA1c_level),
        "blood_glucose_level": _to_float(blood_glucose_level),
    }
    result = _post_json(url, payload)
    # Extract only prediction and explanations
    body = result.get("body", {}) if isinstance(result, dict) else {}
    minimal = {}
    if isinstance(body, dict) and "prediction" in body:
        minimal["prediction"] = body.get("prediction")
    if isinstance(body, dict) and "explanations" in body:
        minimal["explanations"] = body.get("explanations")
    return minimal

if __name__ == "__main__":
    host = "0.0.0.0"
    port = 8005

    # Get local IP address
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"Server running at http://{host}:{port}")
    print(f"Local network URL: http://{local_ip}:{port}")

    mcp.run(
        transport="streamable-http",
        host=host,
        port=port,
        log_level="debug"
    )