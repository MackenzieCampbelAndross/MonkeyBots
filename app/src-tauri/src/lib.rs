#[tauri::command]
fn get_backend_url() -> String {
    "http://127.0.0.1:8765".to_string()
}

#[tauri::command]
fn get_ws_url() -> String {
    "ws://127.0.0.1:8765/ws/simulation".to_string()
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::default()
                .level(log::LevelFilter::Info)
                .build(),
        )
        .invoke_handler(tauri::generate_handler![get_backend_url, get_ws_url])
        .run(tauri::generate_context!())
        .expect("error while running MonkeyBots Tauri application");
}
