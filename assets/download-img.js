$('document').ready(function(){
	$('document').on('click', "#btn-frame-download", function () {
	  var element = $("#graph-collection"); // global variable
	  var getCanvas; // global variable
	  html2canvas(element).then(function (canvas) {
	      //$("#previewImage").append(canvas);
	      getCanvas = canvas;
	    }
	  );
	  var imageData = getCanvas.toDataURL("image/png");
	  // Now browser starts downloading it instead of just showing it
	  var newData = imageData.replace(/^data:image\/png/, "data:application/octet-stream");
	  $("#btn-frame-download").attr("download", "image.png").attr("href", newData);
	});
});
