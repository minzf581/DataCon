import pytest
import asyncio
from core.firestore_manager import firestore_manager

@pytest.mark.asyncio
async def test_firestore_operations():
    """测试 Firestore 基本操作"""
    # 测试数据
    test_data = {
        'name': '测试用户',
        'email': 'test@example.com',
        'age': 25
    }
    
    # 测试集合名称
    collection_name = 'test_users'
    
    try:
        # 创建文档
        doc_id = await firestore_manager.create_document(collection_name, test_data)
        assert doc_id is not None, "文档创建失败"
        
        # 读取文档
        doc = await firestore_manager.get_document(collection_name, doc_id)
        assert doc is not None, "文档读取失败"
        assert doc['name'] == test_data['name'], "文档数据不匹配"
        
        # 更新文档
        update_data = {'age': 26}
        await firestore_manager.update_document(collection_name, doc_id, update_data)
        
        # 验证更新
        updated_doc = await firestore_manager.get_document(collection_name, doc_id)
        assert updated_doc['age'] == 26, "文档更新失败"
        
        # 查询文档
        filters = [('name', '==', '测试用户')]
        docs = await firestore_manager.query_documents(collection_name, filters=filters)
        assert len(docs) > 0, "文档查询失败"
        
        # 删除文档
        await firestore_manager.delete_document(collection_name, doc_id)
        
        # 验证删除
        deleted_doc = await firestore_manager.get_document(collection_name, doc_id)
        assert deleted_doc is None, "文档删除失败"
        
    except Exception as e:
        pytest.fail(f"Firestore 操作失败: {str(e)}")

if __name__ == '__main__':
    asyncio.run(test_firestore_operations()) 