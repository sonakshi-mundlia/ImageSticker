from fastapi import APIRouter, HTTPException, Request
import os

router = APIRouter()

def get_output_dir():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "outputs")


@router.get("/")
def list_output_files(request: Request):
    try:
        output_dir = get_output_dir()
        os.makedirs(output_dir, exist_ok=True)

        files = [
            f for f in os.listdir(output_dir)
            if os.path.isfile(os.path.join(output_dir, f))
        ]

        base_url = str(request.base_url).rstrip("/")
        urls = [f"{base_url}/outputs/{f}" for f in files]

        return {
            "count": len(files),
            "files": files,
            "urls": urls
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))