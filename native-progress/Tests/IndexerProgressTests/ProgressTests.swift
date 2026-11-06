import XCTest
@testable import IndexerProgress
final class ProgressTests: XCTestCase {
 func testHonestCounts() throws {
  let data = Data(#"{"protocol_version":1,"stage":"asr_vlm","current":"A001.mp4","total":5,"completed":2,"failed":1,"started_at":100,"updated_at":110}"#.utf8)
  let value = try JSONDecoder().decode(ProgressStatus.self,from:data)
  XCTAssertEqual(value.remaining,2);XCTAssertEqual(value.label,"Transcribing audio and describing images")
 }
 func testLegacyHasNoInferredCounts() throws {
  let value = try JSONDecoder().decode(ProgressStatus.self,from:Data(#"{"phase":"processing","active":"previous.mp4"}"#.utf8))
  XCTAssertNil(value.current);XCTAssertNil(value.remaining)
 }
}
