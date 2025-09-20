from fastmcp import FastMCP
import socket
import requests
import time
from typing import Dict, Any

mcp = FastMCP("TIC")


@mcp.tool("say_hello")
def say_hello(name: str) -> str:
    """A simple function to say hello."""
    return f"Hello, {name}!"


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
    age: int,
    gender: int,
    height: int,
    weight: int,
    ap_hi: int,
    ap_lo: int,
    cholesterol: int,
    gluc: int,
    smoke: int,
    alco: int,
    active: int,
) -> Dict[str, Any]:
    """Call the cardiovascular model prediction endpoint using explicit args.

    Accepts each expected cardiovascular input as a separate argument
    (rather than a single payload dict). The function constructs the
    payload internally, posts it to the cardio service at
    ``http://localhost:5002/predict`` and returns the response along with
    timing information.

    Args:
        age (int): Age in years.
        gender (int): 1 for male, 0 for female (API contract dependent).
        height (int): Height in cm.
        weight (int): Weight in kg.
        ap_hi (int): Systolic blood pressure (mmHg).
        ap_lo (int): Diastolic blood pressure (mmHg).
        cholesterol (int): Cholesterol category (1,2,3).
        gluc (int): Glucose category (1,2,3).
        smoke (int): Smoking flag (0/1).
        alco (int): Alcohol flag (0/1).
        active (int): Physical activity flag (0/1).

    Returns:
        Dict[str, Any]: Result dictionary returned by ``_post_json``.

    Raises:
        requests.exceptions.RequestException: If the POST fails.
    """
    url = "http://localhost:5002/predict"
    payload = {
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "ap_hi": ap_hi,
        "ap_lo": ap_lo,
        "cholesterol": cholesterol,
        "gluc": gluc,
        "smoke": smoke,
        "alco": alco,
        "active": active,
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
    age: int,
    gender: str,
    hypertension: int,
    heart_disease: int,
    smoking_history: str,
    bmi: float,
    HbA1c_level: float,
    blood_glucose_level: int,
) -> Dict[str, Any]:
    """Call the diabetes model prediction endpoint using explicit args.

    Accepts each expected diabetes input as a separate argument. The
    function constructs the payload internally and posts to
    ``http://localhost:5003/predict`` returning the response plus timing.

    Args:
        age (int): Age in years.
        gender (str): Gender string (e.g., "Male", "Female", "Other").
        hypertension (int): Hypertension flag (0/1).
        heart_disease (int): Heart disease flag (0/1).
        smoking_history (str): Smoking history descriptor.
        bmi (float): Body Mass Index.
        HbA1c_level (float): HbA1c percentage.
        blood_glucose_level (int): Blood glucose in mg/dL.

    Returns:
        Dict[str, Any]: Result dictionary returned by ``_post_json``.

    Raises:
        requests.exceptions.RequestException: If the POST fails.
    """
    url = "http://localhost:5003/predict"
    payload = {
        "age": age,
        "gender": gender,
        "hypertension": hypertension,
        "heart_disease": heart_disease,
        "smoking_history": smoking_history,
        "bmi": bmi,
        "HbA1c_level": HbA1c_level,
        "blood_glucose_level": blood_glucose_level,
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


@mcp.tool("get_predictions")
def get_predictions(
    # Cardiovascular args
    age: int,
    gender: int,
    height: int,
    weight: int,
    ap_hi: int,
    ap_lo: int,
    cholesterol: int,
    gluc: int,
    smoke: int,
    alco: int,
    active: int,
    # Diabetes args
    d_age: int,
    d_gender: str,
    hypertension: int,
    heart_disease: int,
    smoking_history: str,
    bmi: float,
    HbA1c_level: float,
    blood_glucose_level: int,
) -> Dict[str, Any]:
    """Call both APIs using explicit, separate arguments for each field.

    This convenience tool accepts each field required by the cardiovascular
    and diabetes prediction endpoints as individual function arguments.
    It forwards the cardiovascular-related arguments to
    ``call_cardio_api`` and the diabetes-related arguments to
    ``call_diabetes_api`` and returns both responses.

    Returns a dictionary with keys ``"cardio"`` and ``"diabetes"`` that
    contain the respective response dictionaries.
    """
    cardio_res = call_cardio_api(
        age=age,
        gender=gender,
        height=height,
        weight=weight,
        ap_hi=ap_hi,
        ap_lo=ap_lo,
        cholesterol=cholesterol,
        gluc=gluc,
        smoke=smoke,
        alco=alco,
        active=active,
    )

    diabetes_res = call_diabetes_api(
        age=d_age,
        gender=d_gender,
        hypertension=hypertension,
        heart_disease=heart_disease,
        smoking_history=smoking_history,
        bmi=bmi,
        HbA1c_level=HbA1c_level,
        blood_glucose_level=blood_glucose_level,
    )

    # Both helpers already return minimal payloads (prediction + explanations)
    return {"cardio": cardio_res, "diabetes": diabetes_res}


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