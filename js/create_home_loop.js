const { Cluster } = require('puppeteer-cluster');
const gm = require('gm');
const fs = require("fs");
const url = 'http://bscesdust03.bsc.es:9000/daily_dashboard/'
const uniqueId = Date.now().toString(36) + Math.random().toString(36).substring(2);
const imageTemplate = './tmp/' + uniqueId + '_image';

function delay(time) {
 return new Promise(function(resolve) { 
   setTimeout(resolve, time)
 });
}

const RunCluster = async (anim, all) => {
  const cluster = await Cluster.launch({
    concurrency: Cluster.CONCURRENCY_CONTEXT,
    puppeteerOptions: {
        headless: true,
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
        //    '--start-maximized',
        ]
    },
    maxConcurrency: 4,
  });

  await cluster.task(async ({ page, data: args }) => {
      process.stdout.write("ARGS: " + args + "\n");
      var tstep = args[0];
      var all = args[1];
      process.stdout.write("TSTEP: " + tstep + " -- ALL: " + all + "\n");
      await page.setViewport({ width: 1280, height: 768});
      await page.goto(url, {
          waitUntil: 'networkidle0',
      });
      await page.waitForSelector("#graph-collection");
      await page.waitForSelector(".graph-with-slider");
      // const zoom = await page.$$("a.leaflet-control-zoom-out");
      // await zoom.click();
      if (all) {
	try {			
              process.stdout.write("SELECT ALL MODELS\n");
	      for (const model of await page.$$('.custom-control-input')) {
		      const checked = await model.evaluate(elem => elem.checked);
			process.stdout.write("CHECKED BEFORE: " + checked + "\n");
		     if (!checked) {
			await model.click();
		    }
	      }
	} catch (err) {
		process.stdout.write("ERR1: " + err + "\n");
	}
	try {
	      for (const model of await page.$$('.custom-control-input')) {
		      const checked = await model.evaluate(elem => elem.checked);
			process.stdout.write("CHECKED AFTER: " + checked + "\n");
			    }
              process.stdout.write("CLICK APPLY BUTTON\n");
	      const btn = await page.$('#models-apply');
	      await btn.click();  // "button#models-apply");
	      await delay(1000);
	} catch (err) {
		process.stdout.write("ERR2: " + err + "\n");
	}
      }
      var num = "00";
      if (tstep === false) {
         process.stdout.write("CURRENT SELECTION: " + tstep + "\n");
         num = "_curr";
      } else {
         process.stdout.write("CURRENT TSTEP: " + tstep + "\n");
          const steps = await page.$$("span.rc-slider-dot");
          await steps[tstep].click();
          if (tstep<10) {
		num = "0"+tstep;
          } else {
		num = tstep;
          }
      }
      await page.waitForSelector("#graph-collection");
      const graph = await page.$('#graph-collection');
      // remove timeslider 
      await page.waitForSelector(".layout-dropdown");
      process.stdout.write("REMOVING LAYOUT DROPDOWN" + "\n");
      await page.evaluate((sel) => {
          let toRemove = document.querySelector(sel);
          toRemove.parentNode.removeChild(toRemove);
      }, '.layout-dropdown');
      // remove zoom panel 
      process.stdout.write("REMOVING ZOOM PANEL(S)" + "\n");
      await page.waitForSelector(".leaflet-bar");
      await page.evaluate((sel) => {
          let toRemove = document.querySelectorAll(sel);
	  for (let j=0; j<toRemove.length; j++) {
	          toRemove[j].parentNode.removeChild(toRemove[j]);
	  }
      }, '.leaflet-bar');

      //await page.waitForSelector(".graph-with-slider");
      process.stdout.write("TAKE SCREENSHOT" + "\n");
      await graph.screenshot({ path: imageTemplate + num + '.png' });

    });

    if (anim) {
        for (let i=0; i<25; i++) {
		try {
      			process.stdout.write("QUEUEING step:" + i + "\n");
			await cluster.queue([i, all]);
		} catch (err) {
			console.log(err);
      			process.stdout.write("ERROR:" + err + "\n");
		}
	}
    } else {
	process.stdout.write("QUEUEING current:" + anim + "\n");
	    cluster.queue([anim, all]);
    }

    await cluster.idle();
    await cluster.close();
}

var anim = true;
var all = false;

process.stdout.write("START: ANIM" + anim + "ALL" + all + "\n");
RunCluster(anim, all);

//if (anim == true) {
//	function check_file(path) {
//	    process.stdout.write("hello: " + path);
//	    while (!fs.existsSync(path))
//		    setTimeout(() => { }, 500);
//	}
//
//	for (let i=0; i<25; i++) {
//	    if (i<10) {
//	      var num = "0"+i;
//	    }
//	    else {
//	      var num = i;
//	    }
//	    check_file(imageTemplate + num + '.png');
//	}
//
//	gm()
//	.in('image00.png')
//	.in('image01.png')
//	.in('image02.png')
//	.in('image03.png')
//	.in('image04.png')
//	.in('image05.png')
//	.in('image06.png')
//	.in('image07.png')
//	.in('image08.png')
//	.in('image09.png')
//	.in('image10.png')
//	.in('image11.png')
//	.in('image12.png')
//	.in('image13.png')
//	.in('image14.png')
//	.in('image15.png')
//	.in('image16.png')
//	.in('image17.png')
//	.in('image18.png')
//	.in('image19.png')
//	.in('image20.png')
//	.in('image21.png')
//	.in('image22.png')
//	.in('image23.png')
//	.in('image24.png')
//	.delay(25)
//	//.resize(600,600)
//	.write("animated.gif", function(err){
//	  if (err) console.log(err);
//	  console.log("animated.gif created");
//	});
//}
