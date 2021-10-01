
def set_background():
    #create loop in thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    #add new background task here
    asyncio.ensure_future(firstWorker())
    asyncio.ensure_future(secondWorker())
    
    loop.run_forever()