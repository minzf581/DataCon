import asyncio
from dc_core.services.social_sentiment import SocialSentimentService

async def main():
    """获取社交媒体情绪数据"""
    service = SocialSentimentService()
    
    try:
        # 获取比特币的社交媒体情绪
        btc_sentiment = await service.get_social_sentiment('BTC')
        print("\n比特币(BTC)社交媒体情绪:")
        if btc_sentiment['status'] == 'success':
            data = btc_sentiment['data']
            print(f"综合情绪评分: {data['overall']['score']:.2f}")
            print(f"情绪标签: {data['overall']['label']}")
            print(f"置信度: {data['overall']['confidence']:.2f}")
            
            # 显示各平台详细数据
            for platform in ['twitter', 'reddit', 'stocktwits']:
                if data[platform]:
                    print(f"\n{platform.capitalize()}平台数据:")
                    metrics = data[platform]['metrics']
                    counts = metrics['sentiment_counts']
                    ratios = metrics['sentiment_ratio']
                    print(f"看多: {counts['bullish']} ({ratios['bullish']:.2%})")
                    print(f"看空: {counts['bearish']} ({ratios['bearish']:.2%})")
                    print(f"中性: {counts['neutral']} ({ratios['neutral']:.2%})")
        else:
            print(f"获取数据失败: {btc_sentiment.get('error')}")
            
        # 获取特朗普币的社交媒体情绪
        trump_sentiment = await service.get_social_sentiment('TRUMP')
        print("\n特朗普币(TRUMP)社交媒体情绪:")
        if trump_sentiment['status'] == 'success':
            data = trump_sentiment['data']
            print(f"综合情绪评分: {data['overall']['score']:.2f}")
            print(f"情绪标签: {data['overall']['label']}")
            print(f"置信度: {data['overall']['confidence']:.2f}")
            
            # 显示各平台详细数据
            for platform in ['twitter', 'reddit', 'stocktwits']:
                if data[platform]:
                    print(f"\n{platform.capitalize()}平台数据:")
                    metrics = data[platform]['metrics']
                    counts = metrics['sentiment_counts']
                    ratios = metrics['sentiment_ratio']
                    print(f"看多: {counts['bullish']} ({ratios['bullish']:.2%})")
                    print(f"看空: {counts['bearish']} ({ratios['bearish']:.2%})")
                    print(f"中性: {counts['neutral']} ({ratios['neutral']:.2%})")
        else:
            print(f"获取数据失败: {trump_sentiment.get('error')}")
            
    except Exception as e:
        print(f"发生错误: {e}")
    finally:
        await service.close()

if __name__ == '__main__':
    asyncio.run(main()) 