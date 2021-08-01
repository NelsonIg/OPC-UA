import asyncio, time

async def download_data(destination, delay):
    await asyncio.sleep(delay)
    print(f'Downloaded data from {destination}')

async def main():
    print('Download data sequentially')
    t1 = time.perf_counter()
    await download_data('Tokyo', 10)
    await download_data('Munich', 2)
    t2 = time.perf_counter()
    print(f'Downloads took {round(t2-t1)}s')

    print('Download data concurrently')
    task1 = asyncio.create_task(download_data('Tokyo', 10))
    task2 = asyncio.create_task(download_data('Munich', 2))
    t1 = time.perf_counter()
    await task1
    await task2
    t2 = time.perf_counter()
    print(f'Downloads took {round(t2-t1)}s')

asyncio.run(main())