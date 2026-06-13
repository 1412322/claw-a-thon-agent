"""
API Parser Service - Parse Swagger/OpenAPI specs and Postman collections.
"""
import json
import yaml
from typing import Optional
from app.schemas import EndpointInfo, ParsedSpecResponse


def parse_openapi_spec(content: bytes) -> ParsedSpecResponse:
    """
    Parse OpenAPI/Swagger specification (JSON or YAML).

    Args:
        content: Raw bytes of the spec file

    Returns:
        ParsedSpecResponse with list of endpoints
    """
    spec = None
    parse_error = None

    try:
        # Try JSON first
        try:
            text_content = content.decode('utf-8')
            spec = json.loads(text_content)
        except json.JSONDecodeError as e:
            # Try YAML
            try:
                text_content = content.decode('utf-8')
                spec = yaml.safe_load(text_content)
            except Exception as yaml_error:
                parse_error = f"JSON error: {e}, YAML error: {yaml_error}"

    except Exception as e:
        raise ValueError(f"Failed to parse spec file: {e}")

    if parse_error:
        raise ValueError(f"Failed to parse spec file: {parse_error}")

    if not spec:
        raise ValueError("Empty or invalid spec file")

    endpoints = []

    # Handle OpenAPI 3.x
    if 'openapi' in spec:
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoint = _extract_endpoint_info(method, path, details)
                    endpoints.append(endpoint)

    # Handle Swagger 2.0
    elif 'swagger' in spec:
        paths = spec.get('paths', {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if method in ['get', 'post', 'put', 'delete', 'patch']:
                    endpoint = _extract_endpoint_info(method, path, details)
                    endpoints.append(endpoint)

    else:
        raise ValueError("Not a valid OpenAPI/Swagger spec (missing 'openapi' or 'swagger' key)")

    return ParsedSpecResponse(
        source_file="openapi_spec",
        spec_type="openapi",
        total_endpoints=len(endpoints),
        endpoints=endpoints
    )


def parse_postman_collection(content: bytes) -> ParsedSpecResponse:
    """
    Parse Postman collection JSON.

    Args:
        content: Raw bytes of the collection file

    Returns:
        ParsedSpecResponse with list of endpoints
    """
    try:
        collection = json.loads(content.decode('utf-8'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON file: {e}")

    if not collection:
        raise ValueError("Empty or invalid collection file")

    endpoints = []

    # Extract items recursively (handle folders)
    items = _extract_postman_items(collection)

    for item in items:
        request = item.get('request', {})

        # Get method and path
        method = request.get('method', 'GET').upper()
        url_obj = request.get('url', {})

        # Handle different URL formats
        if isinstance(url_obj, str):
            path = url_obj
        elif isinstance(url_obj, dict):
            path = url_obj.get('raw', '')
            if not path:
                path_parts = url_obj.get('path', [])
                path = '/' + '/'.join(path_parts) if path_parts else ''
        else:
            path = '/'

        # Skip if not a valid HTTP method
        if method not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
            continue

        # Extract request body if present
        request_body = None
        body = request.get('body', {})
        if body:
            mode = body.get('mode')
            if mode == 'raw':
                raw_body = body.get('raw', '{}')
                try:
                    request_body = json.loads(raw_body)
                except:
                    request_body = {'raw': raw_body}
            elif mode == 'formdata':
                formdata = body.get('formdata', [])
                request_body = {fd.get('key'): fd.get('value', '') for fd in formdata if fd.get('key')}
            elif mode == 'urlencoded':
                urlencoded = body.get('urlencoded', [])
                request_body = {ue.get('key'): ue.get('value', '') for ue in urlencoded if ue.get('key')}

        # Extract description/summary
        summary = item.get('name', '')
        description = item.get('description', '')

        endpoint = EndpointInfo(
            method=method,
            path=path,
            summary=summary,
            description=description,
            request_body=request_body,
            expected_status=200
        )
        endpoints.append(endpoint)

    return ParsedSpecResponse(
        source_file="postman_collection",
        spec_type="postman",
        total_endpoints=len(endpoints),
        endpoints=endpoints
    )


def _extract_endpoint_info(method: str, path: str, details: dict) -> EndpointInfo:
    """Extract endpoint info from OpenAPI spec details."""
    method_upper = method.upper()

    # Get summary and description
    summary = details.get('summary', '')
    description = details.get('description', '')

    # Extract request body example if available
    request_body = None
    requestBody = details.get('requestBody', {})
    if requestBody:
        content = requestBody.get('content', {})
        json_content = content.get('application/json', {})
        schema = json_content.get('schema', {})
        example = schema.get('example') or schema.get('examples', {}).get('default', {}).get('value')
        if example:
            request_body = example

    # Determine expected status
    responses = details.get('responses', {})
    expected_status = 200
    if '200' in responses:
        expected_status = 200
    elif '201' in responses:
        expected_status = 201

    return EndpointInfo(
        method=method_upper,
        path=path,
        summary=summary,
        description=description,
        request_body=request_body,
        expected_status=expected_status
    )


def _extract_postman_items(collection: dict, items: list = None) -> list:
    """Recursively extract all items from Postman collection (handle folders)."""
    if items is None:
        items = []

    collection_items = collection.get('item', [])

    for item in collection_items:
        # Check if it's a folder (has nested items)
        if item.get('item'):
            # Recursively extract nested items
            _extract_postman_items(item, items)
        else:
            # It's a request
            items.append(item)

    return items
