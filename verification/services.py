from typing import Dict, Any
import numpy as np
from core.models import Dataset
from crypto.zkp import ZKPProtocol
from crypto.gkr import GKRProtocol
import pandas as pd

class VerificationService:
    def __init__(self, dataset: Dataset):
        self.dataset = dataset
        self.zkp_protocol = ZKPProtocol(secret=b'your-secret-key')
        self.gkr_protocol = GKRProtocol()
        
    def generate_zkp_proof(self) -> Dict[str, Any]:
        """生成零知识证明"""
        # 读取数据集
        df = pd.read_csv(self.dataset.file_path)
        
        # 生成数据集特征描述
        statement = self._generate_dataset_statement(df)
        
        # 生成证明
        proof = self.zkp_protocol.generate_proof(statement)
        
        return {
            'commitment': proof.commitment,
            'challenge': proof.challenge,
            'response': proof.response,
            'public_inputs': proof.public_inputs
        }
    
    def verify_gkr_protocol(self) -> bool:
        """验证GKR协议"""
        try:
            # 读取数据集
            df = pd.read_csv(self.dataset.file_path)
            
            # 将数据转换为numpy数组
            data = df.to_numpy()
            
            # 生成计算证明
            proof = self.gkr_protocol.prove_computation(data)
            
            # 验证证明
            return self.gkr_protocol.verify_computation(proof, data)
            
        except Exception as e:
            print(f"GKR验证失败: {str(e)}")
            return False
            
    def _generate_dataset_statement(self, df: pd.DataFrame) -> str:
        """生成数据集描述声明"""
        return f"""
        Dataset: {self.dataset.name}
        Rows: {len(df)}
        Columns: {list(df.columns)}
        Types: {df.dtypes.to_dict()}
        """ 