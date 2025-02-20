from dc_core.services.sentiment_analysis import MarketSentimentService

def main():
    """获取加密货币市场情绪"""
    service = MarketSentimentService()
    
    # 获取比特币市场情绪
    try:
        btc_sentiment = service.get_crypto_sentiment('BTCUSDT')
        print("\n比特币(BTC)市场情绪:")
        print(f"情绪评分: {btc_sentiment['data']['sentiment_score']:.2f}")
        print(f"情绪标签: {btc_sentiment['data']['sentiment_label']}")
        print("详细信息:")
        for detail in btc_sentiment['data']['details']:
            print(f"- {detail}")
    except Exception as e:
        print(f"获取比特币数据失败: {e}")
    
    # 获取特朗普币市场情绪
    try:
        trump_sentiment = service.get_crypto_sentiment('TRUMPUSDT')
        print("\n特朗普币(TRUMP)市场情绪:")
        print(f"情绪评分: {trump_sentiment['data']['sentiment_score']:.2f}")
        print(f"情绪标签: {trump_sentiment['data']['sentiment_label']}")
        print("详细信息:")
        for detail in trump_sentiment['data']['details']:
            print(f"- {detail}")
    except Exception as e:
        print(f"获取特朗普币数据失败: {e}")

if __name__ == '__main__':
    main() 