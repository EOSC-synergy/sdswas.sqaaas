//L_PREFER_CANVAS = true;

//window.dash_clientside = Object.assign({}, window.dash_clientside, {
//    clientside: {
//        download_png_frame: function(clicks) {
//          console.log(clicks);
//          var element = document.getElementById("graph-collection"); // global variable
//          var ret = html2canvas(element, {
//              // allowTaint: true,
//              userCORS: true,
//              onrendered: function (canvas) {
//                 var imgData = canvas.toDataURL('image/png');
//                 var downloadData = imgData.replace(/^data:image\/png/, "data:application/octet-stream");
//         return downloadData;
//                 // console.log(downloadData);
//         console.log($("#frame-download"));
//                 $("#frame-download").attr("data", downloadData);     
//                 //window.open(imgData);
//           }
//          } 
//          );
//     return ret;
////          return getCanvas.replace(/^data:image\/png/, "data:application/octet-stream");
////          //var imageData = getCanvas.toDataURL("image/png");
////          // Now browser starts downloading it instead of just showing it
////          return res  // getCanvas.replace(/^data:image\/png/, "data:application/octet-stream");
//        }
//    }
//});

$(document).ready(function () {
	$(document).on('click', "#btn-img-download", function () {
		var element = document.getElementById("graph-collection"); // global variable
		html2canvas(element, {
                  allowTaint: true,
		  useCORS: true,
		    }).then(function (canvas) {
		    var getCanvas = canvas;
		    var imageData = getCanvas.toDataURL("image/png");
		    // Now browser starts downloading it instead of just showing it
		    var newData = imageData.replace(/^data:image\/png/, "data:application/octet-stream");
		    // console.log("************ newData ************");
		    // console.log(newData);
		    $("#btn-img-download").attr("download", "image.png").attr("href", newData);
	            //window.open(imageData);
		});
	});
});
