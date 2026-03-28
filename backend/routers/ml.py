from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from database import get_db
from models import MLPrediction, AuditLog
from auth import get_current_admin, get_current_hospital_or_admin, get_current_user
import ml_pipeline

router = APIRouter()

_training_status = {"status": "idle", "last_trained": None}


def _run_training(db_url: str = None):
    global _training_status
    _training_status["status"] = "running"
    try:
        results = ml_pipeline.run_full_pipeline()
        _training_status["status"] = "completed"
        _training_status["last_trained"] = datetime.utcnow().isoformat()
        _training_status["results"] = results
    except Exception as e:
        _training_status["status"] = "failed"
        _training_status["error"] = str(e)


@router.post("/train")
async def trigger_training(
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    if _training_status["status"] == "running":
        return {"message": "Training already in progress"}

    background_tasks.add_task(_run_training)
    db.add(AuditLog(user_id=current_user.id, action="ML_TRAINING_TRIGGERED"))
    await db.commit()

    return {"message": "ML training started in background", "status": "running"}


@router.get("/training-status")
async def training_status(current_user=Depends(get_current_hospital_or_admin)):
    return _training_status


@router.get("/predict")
async def get_predictions(current_user=Depends(get_current_user)):
    results = ml_pipeline.load_saved_results()
    if "forecast" not in results:
        raise HTTPException(
            status_code=404,
            detail="No predictions available. Please trigger training first.",
        )
    return {
        "forecast": results.get("forecast", []),
        "metrics": results.get("metrics", {}),
    }


@router.get("/instability-index")
async def get_instability_index(
    region: str = None,
    organ: str = None,
    current_user=Depends(get_current_user),
):
    results = ml_pipeline.load_saved_results()
    odii_data = results.get("odii", [])

    if not odii_data:
        raise HTTPException(
            status_code=404,
            detail="No ODII data available. Please trigger training first.",
        )

    if region:
        odii_data = [d for d in odii_data if d["region"].lower() == region.lower()]
    if organ:
        odii_data = [d for d in odii_data if d["organ_type"].lower() == organ.lower()]

    # Summary stats
    if odii_data:
        avg_odii = sum(d["instability_index"] for d in odii_data) / len(odii_data)
        max_odii = max(odii_data, key=lambda x: x["instability_index"])
    else:
        avg_odii = 0
        max_odii = None

    return {
        "data": odii_data[:100],  # limit response
        "summary": {
            "total_records": len(odii_data),
            "average_odii": round(avg_odii, 4),
            "highest_instability": max_odii,
        },
    }


@router.get("/explain")
async def get_shap_explanations(current_user=Depends(get_current_user)):
    results = ml_pipeline.load_saved_results()
    shap_data = results.get("shap", {})

    if not shap_data:
        raise HTTPException(
            status_code=404,
            detail="No SHAP data available. Please trigger training first.",
        )
    return shap_data


@router.get("/metrics")
async def get_model_metrics(current_user=Depends(get_current_user)):
    results = ml_pipeline.load_saved_results()
    return results.get("metrics", {"message": "No metrics available yet. Run training first."})


@router.get("/fairness")
async def get_fairness_metrics(current_user=Depends(get_current_hospital_or_admin)):
    """Return fairness & bias evaluation across demographic groups."""
    results = ml_pipeline.load_saved_results()
    data = results.get("fairness")
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No fairness data available. Please trigger training first.",
        )
    return data


@router.get("/calibration")
async def get_calibration(current_user=Depends(get_current_hospital_or_admin)):
    """Return model calibration curve and reliability score."""
    results = ml_pipeline.load_saved_results()
    data = results.get("calibration")
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No calibration data available. Please trigger training first.",
        )
    return data


@router.get("/version-history")
async def get_version_history(current_user=Depends(get_current_hospital_or_admin)):
    """Return full history of model training runs and versions."""
    results = ml_pipeline.load_saved_results()
    versions = results.get("model_versions", [])
    return {
        "total_versions": len(versions),
        "versions": versions,
    }
