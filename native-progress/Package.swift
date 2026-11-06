// swift-tools-version: 5.9
import PackageDescription
let package = Package(name: "IndexerProgress", platforms: [.macOS(.v14)], products: [.executable(name: "IndexerProgress", targets: ["IndexerProgress"])], targets: [.executableTarget(name: "IndexerProgress"), .testTarget(name: "IndexerProgressTests", dependencies: ["IndexerProgress"])])
