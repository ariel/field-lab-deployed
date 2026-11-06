import Foundation
struct ProgressStatus: Decodable {
    let protocolVersion: Int?
    let stage: String?
    let current: String?
    let total: Int?
    let completed: Int?
    let failed: Int?
    let elapsed: Double?
    let startedAt: Double?
    let updatedAt: Double?
    let phase: String?
    let lastError: String?
    enum CodingKeys: String, CodingKey {
        case protocolVersion = "protocol_version", stage, current, total, completed, failed, elapsed
        case startedAt = "started_at", updatedAt = "updated_at", phase, lastError = "last_error"
    }
    var remaining: Int? {
        guard let total, let completed, let failed else { return nil }
        return max(0, total - completed - failed)
    }
    var code: String { stage ?? phase ?? "waiting" }
    var label: String {
        switch code {
        case "warming": return "Preparing models"
        case "faces": return "Finding faces"
        case "analysis": return "Analyzing audio and images"
        case "asr_vlm": return "Transcribing audio and describing images"
        case "asr_and_extraction": return "Transcribing audio and extracting images"
        case "vlm_and_extraction": return "Describing images and extracting audio"
        case "asr": return "Transcribing audio"
        case "vlm": return "Describing images"
        case "publication": return "Saving notes"
        case "hashing": return "Checking file"
        case "file_complete": return "File saved"
        case "reconciling": return "Checking unfinished work"
        case "scanning": return "Finding files"
        case "extraction": return "Extracting audio and images"
        case "indexing": return "Updating search"
        case "complete": return "Complete"
        case "idle", "ready": return "Ready"
        case "failed", "error": return "Needs attention"
        case "processing": return "Processing"
        default: return "Waiting"
        }
    }
}
