import asyncio
import logging
from dc_core.services.social_sentiment import SocialSentimentService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """测试Twitter情绪分析"""
    service = SocialSentimentService()
    
    try:
        # 获取比特币情绪数据
        logger.info("获取BTC情绪数据...")
        btc_sentiment = await service.get_social_sentiment('BTC')
        if btc_sentiment['status'] == 'success':
            data = btc_sentiment['data']
            logger.info(f"BTC综合情绪: 分数={data['overall']['score']:.2f}, "
                       f"标签={data['overall']['label']}, "
                       f"置信度={data['overall']['confidence']:.2f}")
            
            # 输出Twitter详细数据
            if data['twitter']:
                metrics = data['twitter']['metrics']
                logger.info("\nTwitter数据:")
                logger.info(f"情绪计数: {metrics['sentiment_counts']}")
                logger.info(f"情绪比例: {metrics['sentiment_ratio']}")
            else:
                logger.warning("Twitter数据获取失败")
        
        # 获取Trump Coin情绪数据
        logger.info("\n获取TRUMP情绪数据...")
        trump_sentiment = await service.get_social_sentiment('TRUMP')
        if trump_sentiment['status'] == 'success':
            data = trump_sentiment['data']
            logger.info(f"TRUMP综合情绪: 分数={data['overall']['score']:.2f}, "
                       f"标签={data['overall']['label']}, "
                       f"置信度={data['overall']['confidence']:.2f}")
            
            # 输出Twitter详细数据
            if data['twitter']:
                metrics = data['twitter']['metrics']
                logger.info("\nTwitter数据:")
                logger.info(f"情绪计数: {metrics['sentiment_counts']}")
                logger.info(f"情绪比例: {metrics['sentiment_ratio']}")
            else:
                logger.warning("Twitter数据获取失败")
                    
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
    finally:
        await service.close()

if __name__ == '__main__':
    asyncio.run(main()) 