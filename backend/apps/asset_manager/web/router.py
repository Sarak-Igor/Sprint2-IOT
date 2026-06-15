from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any
from uuid import UUID
import copy
from sqlalchemy.orm.attributes import flag_modified

from backend.shared_infra.database_client.postgresql import get_db
from backend.apps.asset_manager.domain.entities import (
    MotorModel, DataVariable, SensorHardware, ActiveAsset, TelemetryMapping
)
from backend.apps.asset_manager.infrastructure.repository import AssetRepository
from backend.apps.asset_manager.infrastructure.models import (
    MotorModelDB, DataVariableDB, SensorHardwareDB, ActiveAssetDB, 
    TelemetryMappingDB, OperationalAnomalyDB
)

router = APIRouter(prefix="/assets", tags=["Asset Manager"])

@router.get("/models", response_model=List[MotorModel])
async def list_models(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    models = await repo.motors.get_all()
    return models

@router.post("/models", response_model=MotorModel)
async def create_model(model: MotorModel, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    db_model = MotorModelDB(**model.dict())
    return await repo.motors.create(db_model)

@router.get("/variables", response_model=List[DataVariable])
async def list_variables(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    return await repo.variables.get_all()

@router.post("/variables", response_model=DataVariable)
async def create_variable(var: DataVariable, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    db_var = DataVariableDB(**var.dict())
    return await repo.variables.create(db_var)

@router.get("/sensors", response_model=List[SensorHardware])
async def list_sensors(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    return await repo.sensors.get_all()

@router.post("/sensors", response_model=SensorHardware)
async def create_sensor(sensor: SensorHardware, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    db_sensor = SensorHardwareDB(**sensor.dict())
    return await repo.sensors.create(db_sensor)

@router.get("/active", response_model=List[ActiveAsset])
async def list_active_assets(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    return await repo.assets.get_all()

@router.post("/active", response_model=ActiveAsset)
async def create_active_asset(asset: ActiveAsset, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    
    # Se não houver thresholds aplicados, tentamos herdar do modelo de motor
    if not asset.applied_thresholds:
        motor_model = await repo.motors.get_by_id(asset.motor_model_id)
        if motor_model and motor_model.default_thresholds:
            asset.applied_thresholds = motor_model.default_thresholds

    db_asset = ActiveAssetDB(**asset.dict())
    created_asset = await repo.assets.create(db_asset)
    
    # --- PROVISIONAMENTO AUTOMÁTICO DE TELEMETRIA ---
    # Para que todo Gêmeo Digital seja simulado automaticamente, criamos
    # mapeamentos para todas as variáveis existentes usando um sensor padrão.
    
    try:
        # 1. Buscar todas as variáveis cadastradas
        vars_res = await db.execute(select(DataVariableDB))
        variables = vars_res.scalars().all()
        
        # 2. Buscar um sensor padrão para o provisionamento (ex: IQ-Next)
        sensor_res = await db.execute(select(SensorHardwareDB).limit(1))
        default_sensor = sensor_res.scalar_one_or_none()
        
        if default_sensor and variables:
            for var in variables:
                # Gerar tópico MQTT amigável e único
                var_slug = var.name.lower().replace(" ", "_").replace("(", "").replace(")", "").replace("ç", "c").replace("ã", "a")
                asset_slug = created_asset.name.lower().replace(" ", "_")
                topic = f"Forzy/telemetry/{asset_slug}/{var_slug}"
                
                mapping = TelemetryMappingDB(
                    asset_id=created_asset.id,
                    variable_id=var.id,
                    sensor_id=default_sensor.id,
                    mqtt_topic=topic
                )
                db.add(mapping)
            
            await db.commit()
    except Exception as e:
        print(f"[PROVISIONING] Erro ao criar mapeamentos automáticos: {e}")
        # Não falhamos a criação do ativo se o mapeamento falhar, mas logamos o erro
    
    return created_asset

@router.delete("/active/{id}")
async def delete_active_asset(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    success = await repo.assets.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"message": "Asset deleted successfully"}
    
@router.patch("/active/{id}")
async def update_active_asset(id: UUID, updates: Dict[str, Any], db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    
    existing = await repo.assets.get_by_id(id)
    if not existing:
        raise HTTPException(status_code=404, detail="Asset not found")

    # Se estiver atualizando thresholds, fazemos o merge e garantimos a detecção de mudança
    if "applied_thresholds" in updates:
        print(f"[DEBUG] Atualizando thresholds para ativo {id}")
        # Deep copy para garantir que não estamos alterando o objeto original em memória antes do commit
        current_thresholds = existing.applied_thresholds or {}
        new_thresholds = copy.deepcopy(current_thresholds)
        
        # Merge das atualizações de forma segura
        incoming = updates["applied_thresholds"]
        for var_id, values in incoming.items():
            if var_id not in new_thresholds:
                new_thresholds[var_id] = {}
            
            # Garantir que os valores sejam numéricos
            clean_values = {}
            for k, v in values.items():
                if v == "" or v is None:
                    clean_values[k] = None
                else:
                    try:
                        clean_values[k] = float(v)
                    except (ValueError, TypeError):
                        clean_values[k] = None
            
            new_thresholds[var_id].update(clean_values)
            
            # Validação básica de sanidade
            t = new_thresholds[var_id]
            nom = t.get("nominal")
            war = t.get("warning")
            crit = t.get("critical")
            
            if nom is not None and war is not None and nom > war:
                raise HTTPException(status_code=400, detail=f"Threshold nominal ({nom}) não pode ser maior que o de aviso ({war})")
            if war is not None and crit is not None and war > crit:
                raise HTTPException(status_code=400, detail=f"Threshold de aviso ({war}) não pode ser maior que o crítico ({crit})")
        
        print(f"[DEBUG] Novos thresholds: {new_thresholds}")
        existing.applied_thresholds = new_thresholds
        # Notifica o SQLAlchemy que o campo JSON mudou explicitamente
        flag_modified(existing, "applied_thresholds")

    # Aplica outras atualizações
    for key, value in updates.items():
        if key != "applied_thresholds" and hasattr(existing, key):
            setattr(existing, key, value)

    try:
        await db.commit()
        await db.refresh(existing)
        print(f"[DEBUG] Ativo {id} atualizado e persistido com sucesso.")
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Falha ao persistir ativo {id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao salvar no banco de dados: {str(e)}")
        
    return existing

@router.delete("/models/{id}")
async def delete_model(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    success = await repo.motors.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted successfully"}

@router.delete("/variables/{id}")
async def delete_variable(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    success = await repo.variables.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Variable not found")
    return {"message": "Variable deleted successfully"}

@router.delete("/sensors/{id}")
async def delete_sensor(id: UUID, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    success = await repo.sensors.delete(id)
    if not success:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return {"message": "Sensor deleted successfully"}


@router.post("/mappings", response_model=TelemetryMapping)
async def create_mapping(mapping: TelemetryMapping, db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    db_mapping = TelemetryMappingDB(**mapping.dict())
    return await repo.mappings.create(db_mapping)

@router.get("/dashboard")
async def get_dashboard_data(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    assets = await repo.assets.get_all()
    
    dashboard_assets = []
    for asset in assets:
        result = await db.execute(
            select(TelemetryMappingDB).where(TelemetryMappingDB.asset_id == asset.id)
        )
        mappings = result.scalars().all()
        
        mapped_sensors = []
        for mapping in mappings:
            var = await repo.variables.get_by_id(mapping.variable_id)
            sensor = await repo.sensors.get_by_id(mapping.sensor_id)
            
            # Busca o threshold específico para esta variável no ativo
            # Estrutura: { "var_id_string": { "nominal": 70, "warning": 80, "critical": 90 } }
            asset_thresholds = asset.applied_thresholds or {}
            var_threshold = asset_thresholds.get(str(mapping.variable_id), {})
            
            mapped_sensors.append({
                "variable": var.name if var else "Unknown",
                "variable_id": str(mapping.variable_id),
                "unit": var.unit if var else "",
                "topic": mapping.mqtt_topic,
                "sensor_model": sensor.model_name if sensor else "Unknown",
                "thresholds": var_threshold
            })
            
        motor_model = await repo.motors.get_by_id(asset.motor_model_id)
        
        dashboard_assets.append({
            "id": str(asset.id),
            "name": asset.name,
            "location": asset.location,
            "status": asset.status,
            "motor_model": motor_model or { "brand": "Unknown", "model": "Unknown", "id": str(asset.motor_model_id) },
            "applied_thresholds": asset.applied_thresholds,
            "sensors": mapped_sensors
        })
        
    return dashboard_assets

@router.get("/anomalies")
async def get_anomalies(db: AsyncSession = Depends(get_db)):
    repo = AssetRepository(db)
    # Busca as 50 anomalias mais recentes
    result = await db.execute(
        select(OperationalAnomalyDB)
        .order_by(OperationalAnomalyDB.timestamp.desc())
        .limit(50)
    )
    anomalies = result.scalars().all()
    
    formatted_anomalies = []
    for anom in anomalies:
        asset = await repo.assets.get_by_id(anom.asset_id)
        var = await repo.variables.get_by_id(anom.variable_id)
        
        formatted_anomalies.append({
            "id": str(anom.id),
            "asset_name": asset.name if asset else "Unknown",
            "variable_name": var.name if var else "Unknown",
            "value": anom.value,
            "severity": anom.severity,
            "threshold": anom.threshold_value,
            "timestamp": anom.timestamp.isoformat(),
            "is_resolved": anom.is_resolved
        })
        
    return formatted_anomalies
