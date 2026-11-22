def disconnect_lobby(window):
    if window.client:
        window.client.close()
    
    if window.host_manager:
        window.host_manager.close()