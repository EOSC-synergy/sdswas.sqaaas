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
    $(document).on('click', "#btn-frame-download", function () {
        var element = document.getElementById("graph-collection"); // global variable
        if (element == null) {
           element = document.getElementById("prob-graph"); // global variable
           if (element == null) {
               element = document.getElementById("was-graph"); // global variable
           }
        }
        getCanvas(element);
    });

    $(document).on('click', "#btn-all-frame-download", function () {
    var models = document.getElementsByClassName("custom-control-input");
        for (var i=0; i<models.length; i++) {
      if (models[i].checked == false)
            models[i].click();
        }
        var btn = document.getElementById("models-apply");
        btn.click();
        setTimeout (function () {
            var element = document.getElementById("graph-collection"); // global variable
            if (element == null) {
               element = document.getElementById("prob-graph"); // global variable
               if (element == null) {
                   element = document.getElementById("was-graph"); // global variable
               }
            }
            getCanvas(element);
        }, 1700);
    });
});

function getCanvas(element) {
	window.scrollTo(0, 0);
        html2canvas(element, {
          allowTaint: true,
          useCORS: true,
	  //scrollX: 0, // -window.scrollX,
          //scrollY: 0, //-window.scrollY,
          //windowWidth: document.documentElement.offsetWidth,
          //windowHeight: element.scrollHeight,
          async: false,
          width: element.clientWidth,
          height: element.clientHeight,
          logging: true,
          imageTimeout: 0,
	  onclone: (doc) => {
               //this is the part that solved the displacement of highlighted portion on the map
            var svgs = doc.querySelectorAll('svg.leaflet-zoom-animated');
            for (var j=0; j<svgs.length; j++) {
                 svg = svgs[j];
                const matrixValues = svg.style.transform.match(/matrix.*\((.+)\)/)[1].split(', ');
		svg.style.transform = `none`;
		svg.style.left = `${matrixValues[4]}px`;
		svg.style.top = `${matrixValues[5]}px`;
	    }
      }
    }).then(function (canvas) {
            saveAs(canvas.toDataURL(), 'image.png');
    });
}

function saveAs(uri, filename) {
  var link = document.createElement('a');
  if (typeof link.download === 'string') {
    link.href = uri;
    link.download = filename;

    //Firefox requires the link to be in the body
    document.body.appendChild(link);

    //simulate click
    link.click();

    //remove the link when done
    document.body.removeChild(link);
  } else {
    window.open(uri);
  }
}
