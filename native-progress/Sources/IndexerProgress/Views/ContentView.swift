import SwiftUI
import AppKit
struct ContentView: View {
    let client: ProgressClient
    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text(client.status?.label ?? "Waiting for AI Indexer").font(.headline)
            if let current = client.status?.current, !current.isEmpty { Text(current).lineLimit(3).textSelection(.enabled) }
            if let total = client.status?.total, let done = client.status?.completed, let failed = client.status?.failed {
                ProgressView(value: Double(min(total,done+failed)), total: Double(max(1,total)))
                Text("\(done) completed · \(max(0,total-done-failed)) remaining · \(failed) failed").foregroundStyle(.secondary)
            } else if !["idle","ready","complete","failed","error"].contains(client.status?.code ?? "") { ProgressView().controlSize(.small) }
            TimelineView(.periodic(from: .now, by: 1)) { timeline in
                if let start = client.status?.startedAt {
                    let elapsed = ["idle","complete","failed"].contains(client.status?.code ?? "") ? client.status?.elapsed ?? 0 : max(0,timeline.date.timeIntervalSince1970-start)
                    Text("Elapsed \(Int(elapsed)/60)m \(Int(elapsed)%60)s").monospacedDigit().foregroundStyle(.secondary)
                }
            }
            if let error = client.error ?? client.status?.lastError { Text(error).foregroundStyle(.red).textSelection(.enabled) }
            TimelineView(.periodic(from:.now,by:1)) { context in
                if let last = client.lastReceived, context.date.timeIntervalSince(last)>5 { Text("Updates delayed").foregroundStyle(.secondary) }
            }
            HStack {
                Button("Open Library") { NSWorkspace.shared.open(client.libraryURL) }
                Button("Reveal Ingests") { NSWorkspace.shared.open(client.ingestsURL) }
            }
        }.padding(24).frame(width:440).fixedSize(horizontal:false,vertical:true).task { await client.poll() }
    }
}
