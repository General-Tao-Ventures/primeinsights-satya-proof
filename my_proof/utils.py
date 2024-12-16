import requests
from typing import Dict, Any

def remote_log(config: Dict[str, Any], content: str) -> None:
    if config.get('remote_log_enabled', False) is False:
        return
    
    tee_api_endpoint = config.get('tee_api_endpoint')
    prime_api_key = config.get('prime_api_key')
    
    headers = {
        "X-API-Key": prime_api_key
    }
    requests.post(
        f"{tee_api_endpoint}/log",
        headers=headers,
        json={"proof_key": config['proof_key'], "log_content": content}
    )
