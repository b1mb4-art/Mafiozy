def disconnect_lobby(window):
    if window.client:
        window.client.close()
        window.client = None
    
    if window.host_manager:
        window.host_manager.close()
        window.host_manager = None