import Foundation
import Vision
import ImageIO
import CoreGraphics
let start = Date()
let args=CommandLine.arguments
let input=URL(fileURLWithPath:args[1]);let output=URL(fileURLWithPath:args[2]);let count=args.count>3 ? Int(args[3])! : 12
let data=try Data(contentsOf:input)
let manifest=try JSONSerialization.jsonObject(with:data) as! [String:Any]
let frames=manifest["frames"] as! [[String:Any]]
var observations:[VNFeaturePrintObservation]=[]
var valid:[[String:Any]]=[]
func isBlank(_ path:String)->Bool {
 guard let src=CGImageSourceCreateWithURL(URL(fileURLWithPath:path) as CFURL,nil),let im=CGImageSourceCreateThumbnailAtIndex(src,0,[kCGImageSourceCreateThumbnailFromImageAlways:true,kCGImageSourceThumbnailMaxPixelSize:16] as CFDictionary) else{return false}
 var pixels=[UInt8](repeating:0,count:16*16*4)
 guard let ctx=CGContext(data:&pixels,width:16,height:16,bitsPerComponent:8,bytesPerRow:64,space:CGColorSpaceCreateDeviceRGB(),bitmapInfo:CGImageAlphaInfo.noneSkipLast.rawValue) else{return false}
 ctx.draw(im,in:CGRect(x:0,y:0,width:16,height:16))
 return (0..<16*16).allSatisfy{pixels[$0*4]<12 && pixels[$0*4+1]<12 && pixels[$0*4+2]<12}
}
for frame in frames {
 let path=frame["image"] as! String
 if isBlank(path){continue}
 let request=VNGenerateImageFeaturePrintRequest()
 request.usesCPUOnly=true
 try VNImageRequestHandler(url:URL(fileURLWithPath:path),options:[:]).perform([request])
 if let obs=request.results?.first as? VNFeaturePrintObservation {observations.append(obs);valid.append(frame)}
}
let featureSeconds=Date().timeIntervalSince(start)
let n=observations.count
var distances=Array(repeating:Array(repeating:Float(0),count:n),count:n)
var nonzero:[Float]=[]
for i in 0..<n {for j in (i+1)..<n {var d:Float=0;try observations[i].computeDistance(&d,to:observations[j]);distances[i][j]=d;distances[j][i]=d;nonzero.append(d)}}
let median:Float = max(nonzero.isEmpty ? 1 : nonzero.sorted()[nonzero.count/2], 0.000001)
let similarities=distances.map {$0.map {exp(-Double($0)/Double(median))}}
var selected:[Int]=[]
var coverage=Array(repeating:0.0,count:n)
var local=Array(repeating:0.0,count:n)
for i in 0..<n {
 var neighbors:[Int]=[]
 if i>0{neighbors.append(i-1)}
 if i+1<n{neighbors.append(i+1)}
 local[i]=neighbors.map{Double(distances[i][$0])/Double(median)}.min() ?? 0
}
for _ in 0..<min(count,n) {
 var best = -1;var bestScore = -Double.infinity
 for c in 0..<n where !selected.contains(c) {
  var gain=0.0
  for i in 0..<n {gain += max(0,similarities[i][c]-coverage[i])}
  var score=gain/Double(n)+0.2*local[c]
  if !selected.isEmpty {
   let t=valid[c]["seconds"] as! Double
   let gap=selected.map{abs(t-(valid[$0]["seconds"] as! Double))}.min()!
   score *= min(gap/2,1)
  }
  if score>bestScore {bestScore=score;best=c}
 }
 selected.append(best)
 for i in 0..<n {coverage[i]=max(coverage[i],similarities[i][best])}
}
selected.sort()
let result:[String:Any]=["feature_seconds":featureSeconds,"total_seconds":Date().timeIntervalSince(start),"frames":valid,"selected_indices":selected,"selected_frames":selected.map{valid[$0]},"distances":distances,"method":"CPU Vision featureprints + local novelty + facility-location coverage + temporal spacing"]
try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]).write(to:output)
print("features \(featureSeconds), total \(Date().timeIntervalSince(start)); times \(selected.map{valid[$0]["seconds"]!})")
