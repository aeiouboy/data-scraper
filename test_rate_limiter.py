"""
Test script for rate limiting and request queuing
"""
import asyncio
import time
from app.core.rate_limiter import RateLimiter, RateLimitConfig, RequestQueue


async def simulate_request(rate_limiter: RateLimiter, retailer: str, request_id: int):
    """Simulate a scraping request"""
    start_time = time.time()
    
    # Use rate limiter
    async with rate_limiter.limit(retailer_code=retailer) as _:
        # Simulate request processing
        await asyncio.sleep(0.1)  # Simulate 100ms request
        
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"[{retailer}] Request {request_id} completed in {duration:.2f}s")
    return duration


async def test_rate_limiting():
    """Test rate limiting functionality"""
    print("\n" + "="*60)
    print("Rate Limiting Test")
    print("="*60)
    
    # Create rate limiter with custom configs
    rate_limiter = RateLimiter()
    
    # Configure aggressive limits for testing
    rate_limiter.configure_retailer("TEST", RateLimitConfig(
        requests_per_second=2.0,  # 2 requests per second
        requests_per_minute=30,
        requests_per_hour=1000,
        burst_size=3,  # Allow 3 requests burst
        cooldown_seconds=0.1
    ))
    
    # Set concurrent limit
    rate_limiter.set_concurrent_limit("TEST", 2)
    
    print("\nConfiguration:")
    print("- Rate: 2 requests/second")
    print("- Burst: 3 requests")
    print("- Concurrent: 2 requests")
    print("- Cooldown: 0.1s")
    
    # Test 1: Burst requests
    print("\n--- Test 1: Burst Requests ---")
    start = time.time()
    
    tasks = []
    for i in range(5):
        task = simulate_request(rate_limiter, "TEST", i)
        tasks.append(task)
    
    durations = await asyncio.gather(*tasks)
    total_time = time.time() - start
    
    print(f"\nTotal time for 5 requests: {total_time:.2f}s")
    print(f"Average duration: {sum(durations)/len(durations):.2f}s")
    
    # Show statistics
    stats = rate_limiter.get_stats("TEST")
    print(f"\nStatistics:")
    print(f"- Total requests: {stats.total_requests}")
    print(f"- Throttled requests: {stats.throttled_requests}")
    print(f"- Total wait time: {stats.total_wait_time:.2f}s")
    print(f"- Success rate: {stats.get_success_rate():.1f}%")
    
    # Test 2: Priority requests
    print("\n--- Test 2: Priority Requests ---")
    rate_limiter.reset_stats("TEST")
    
    async def priority_request(priority: str, req_id: int):
        start = time.time()
        wait_time = await rate_limiter.acquire("TEST", priority=priority)
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        duration = time.time() - start
        print(f"[{priority}] Request {req_id} waited {duration:.2f}s")
        return duration
    
    # Submit mixed priority requests
    tasks = []
    tasks.append(priority_request("high", 1))
    tasks.append(priority_request("low", 2))
    tasks.append(priority_request("high", 3))
    tasks.append(priority_request("normal", 4))
    tasks.append(priority_request("low", 5))
    
    await asyncio.gather(*tasks)
    
    # Test 3: Request Queue
    print("\n--- Test 3: Request Queue ---")
    queue = RequestQueue(max_size=10)
    
    # Add requests to queue
    for i in range(6):
        priority = ["high", "normal", "low"][i % 3]
        await queue.put({"id": f"req_{i}", "url": f"http://example.com/{i}"}, priority)
    
    print("\nQueue status after adding:")
    print(queue.get_stats())
    
    # Process requests
    print("\nProcessing requests in priority order:")
    processed = []
    while True:
        request = await queue.get()
        if not request:
            break
        processed.append(request)
        print(f"- {request['id']} (priority: {request['priority']}, queue_time: {request['queue_time']:.3f}s)")
        queue.mark_completed(request['id'], success=True)
    
    print("\nQueue status after processing:")
    print(queue.get_stats())
    
    # Show all rate limiter stats
    print("\n--- Final Statistics ---")
    all_stats = rate_limiter.get_all_stats()
    for scope, stats in all_stats.items():
        print(f"\n{scope}:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    print("\n" + "="*60)
    print("Test completed!")
    print("="*60)


async def test_multi_retailer():
    """Test multi-retailer rate limiting"""
    print("\n" + "="*60)
    print("Multi-Retailer Rate Limiting Test")
    print("="*60)
    
    # Use global rate limiter
    from app.core.rate_limiter import global_rate_limiter
    
    retailers = ["HP", "TWD", "GH"]
    
    async def retailer_requests(retailer: str, count: int):
        print(f"\n{retailer}: Starting {count} requests")
        start = time.time()
        
        tasks = []
        for i in range(count):
            task = simulate_request(global_rate_limiter, retailer, i)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        total = time.time() - start
        print(f"{retailer}: Completed in {total:.2f}s")
        
        stats = global_rate_limiter.get_stats(retailer)
        print(f"{retailer}: Throttled {stats.throttled_requests}/{stats.total_requests} requests")
    
    # Run requests for all retailers concurrently
    await asyncio.gather(
        retailer_requests("HP", 10),
        retailer_requests("TWD", 8),
        retailer_requests("GH", 5)
    )
    
    print("\n" + "="*60)
    print("Multi-retailer test completed!")
    print("="*60)


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_rate_limiting())
    asyncio.run(test_multi_retailer())