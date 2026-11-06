import Foundation
import Observation
@MainActor @Observable final class ProgressClient {
    var status: ProgressStatus?
    var error: String?
    var lastReceived: Date?
    let endpoint: URL
    let libraryURL: URL
    let ingestsURL: URL
    init() {
        let args = ProcessInfo.processInfo.arguments
        let value = args.firstIndex(of: "--status-url").flatMap { $0 + 1 < args.count ? args[$0 + 1] : nil } ?? "http://127.0.0.1:8766/api/status"
        func option(_ name: String, fallback: String) -> String { args.firstIndex(of:name).flatMap { $0+1 < args.count ? args[$0+1] : nil } ?? fallback }
        let library = URL(string:option("--library-url",fallback:"http://127.0.0.1:8766/"))
        libraryURL = library.flatMap { $0.scheme == "http" && ["127.0.0.1","localhost"].contains($0.host ?? "") ? $0 : nil } ?? URL(string:"http://127.0.0.1:8766/")!
        ingestsURL = URL(fileURLWithPath:option("--ingests-path",fallback:FileManager.default.homeDirectoryForCurrentUser.path),isDirectory:true)
        let candidate = URL(string: value)
        endpoint = candidate.flatMap { $0.scheme == "http" && ["127.0.0.1", "localhost"].contains($0.host ?? "") ? $0 : nil } ?? URL(string:"http://127.0.0.1:8766/api/status")!
    }
    func poll() async {
        while !Task.isCancelled {
            do {
                var request = URLRequest(url: endpoint, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 3)
                request.httpMethod = "GET"
                let (data,response) = try await URLSession.shared.data(for: request)
                guard (response as? HTTPURLResponse)?.statusCode == 200 else { throw URLError(.badServerResponse) }
                status = try JSONDecoder().decode(ProgressStatus.self, from: data)
                lastReceived = Date(); error = nil
            } catch { self.error = "Status unavailable: \(error.localizedDescription)" }
            try? await Task.sleep(for: .seconds(1))
        }
    }
}
