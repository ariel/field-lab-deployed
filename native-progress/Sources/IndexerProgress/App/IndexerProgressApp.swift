import SwiftUI
import AppKit
final class Delegate: NSObject, NSApplicationDelegate {
    func applicationDidFinishLaunching(_ notification: Notification) {
        NSApp.setActivationPolicy(.regular); NSApp.activate(ignoringOtherApps: true)
    }
}
@main struct IndexerProgressApp: App {
    @NSApplicationDelegateAdaptor(Delegate.self) var delegate
    @State private var client = ProgressClient()
    var body: some Scene { WindowGroup("AI Indexer") { ContentView(client:client) }.windowResizability(.contentSize) }
}
