from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect
from services import llm_results
from utils import logger
from middleware.auth import get_current_user
from typing import Dict
from models import get_db, User
from sqlalchemy.orm import Session
router = APIRouter()

connected_clients: Dict[str, WebSocket] = {}

@router.websocket("/ws/test")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    current_user = await get_current_user(websocket=websocket)
    if not current_user:
        return
    
    try:
        await websocket.accept()
        
        logger.info(f"current_user: {current_user}")
        user = db.query(User).filter(User.id == current_user["user"]).first()
        
        if not user:
            await websocket.close(code=4003, reason="User not found")
            return
            
        connected_clients[str(user.id)] = websocket
        logger.info(f"user {user.id} connected")
        
        try:
            while True:
                data = await websocket.receive_text()
                logger.info(f"User {user.id}: {data}")
                
                response = f"server received: {data}"
                await websocket.send_text(response)
                
        except WebSocketDisconnect:
            connected_clients.pop(str(user.id), None)
            logger.info(f"User {user.id} disconnected")
            
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        try:
            await websocket.close(code=4000)
        except:
            pass
        if user:
            connected_clients.pop(str(user.id), None)

@router.get("/test")
async def test():
    logger.info("test")
    return "test"

owa = """
{'group_descriptive_stats': {'Home': {'ci_lower': 0.9949838755556591,
                                         'ci_upper': 2.3383494577776744,
                                         'mean': 1.6666666666666667,
                                         'n': 6,
                                         'sd': 0.816496580927726,
                                         'se': 0.33333333333333337},
                                'School': {'ci_lower': 3.6616505422223256,
                                         'ci_upper': 5.0050161244443405,
                                         'mean': 4.333333333333333,
                                         'n': 6,
                                         'sd': 0.816496580927726,
                                         'se': 0.33333333333333337},
                                'Cafe': {'ci_lower': 6.547405731282017,
                                         'ci_upper': 7.785927602051317,
                                         'mean': 7.166666666666667,
                                         'n': 6,
                                         'sd': 0.752772652709081,
                                         'se': 0.3073181485764296}},
     'test_stats': {'between_df': 2.0,
                    'between_f': 71.6666666666667,
                    'between_mean_sq': 45.3888888888889,
                    'between_sig': 2.1081027807666718e-08,
                    'between_sum_sq': 90.7777777777778,
                    'conf_level': 0.95,
                    'total_df': 17.0,
                    'total_sum_sq': 100.2777777777778,
                    'within_df': 15.0,
                    'within_mean_sq': 0.6333333333333332,
                    'within_sum_sq': 9.499999999999998},
     'total_descriptive_stats': {'ci_lower': 3.3930416685103193,
                                 'ci_upper': 5.384736109267459,
                                 'mean': 4.388888888888889,
                                 'n': 18,
                                 'sd': 2.42872246468334,
                                 'se': 0.5724553747992317}}
"""

@router.get("/test/output/results")
async def output_results():
    logger.info("output_results")
    return llm_results("owa", owa)

