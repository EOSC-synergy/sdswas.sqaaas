const { Cluster } = require('puppeteer-cluster');
const util = require('util');
const url = 'http://bscesdust03.bsc.es:9000/daily_dashboard/'
const uniqueId = Date.now().toString(36) + Math.random().toString(36).substring(2);
// const imageTemplate = '/data/daily_dashboard/comparison/';  // + uniqueId + '_image';

function delay(time) {
 return new Promise(function(resolve) { 
   setTimeout(resolve, time)
 });
}

const RunCluster = async (anim, curmodel, seldate, variable) => {
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
      var curmodel = args[1];
      var seldate = args[2];
      var variable = args[3];
      process.stdout.write("TSTEP: " + tstep + " -- MOD: " + curmodel + " -- DATE: " + seldate + " -- VAR: " + variable + "\n");
      await page.setViewport({ width: 1280, height: 768});
      await page.goto(url, {
          waitUntil: 'networkidle0',
      });
      await page.waitForSelector("#graph-collection");
      await page.waitForSelector(".graph-with-slider");
      // select variable
      if (variable !== "OD550_DUST") {
        try {            
      		const sel = await page.$('#variable-dropdown-forecast');
		sel.click();
		await page.waitForSelector(".Select-menu-outer");
		for (const option of await page.$$('.VirtualizedSelectOption')) {
			const curopt = await option.evaluate(elem => elem.innerHTML);
			process.stdout.write("****" +  curopt + "****\n");
			if (curopt === 'Concentration') {
				option.click();
				break;
			}
		}
	} catch (err) {
            process.stdout.write("ERR0: " + err + "\n");
	}
      }
      // select all models 
      if (curmodel === "all") {
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
      }
      // select only one model 
      else {
        try {            
                  process.stdout.write("SELECT MODEL: " + curmodel + "\n");
              for (const model of await page.$$('.custom-control-input')) {
                  const checked = await model.evaluate(elem => elem.checked);
                process.stdout.write("CHECKED BEFORE: " + checked + "\n");
                  const value = await model.evaluate(elem => elem.value);
                process.stdout.write("VALUE: " + value + "\n");
                if (!checked && value === curmodel) {
                await model.click();
                }
                if (checked && value !== curmodel) {
                await model.click();
                }
              }
        } catch (err) {
            process.stdout.write("ERR1: " + err + "\n");
        }
      }
      // apply button
      try {
            for (const model of await page.$$('.custom-control-input')) {
                const checked = await model.evaluate(elem => elem.checked);
              process.stdout.write("CHECKED AFTER: " + checked + "\n");
            }
            process.stdout.write("CLICK APPLY BUTTON\n");
            const btn = await page.$('#models-apply');
            await btn.click();  // "button#models-apply");
            await delay(500);
      } catch (err) {
          process.stdout.write("ERR2: " + err + "\n");
      }
      // select date
//      if (seldate !== "none") {
//        try {
//         await page.waitForSelector('input#date');
//         const curdate = await page.evaluate(() => document.querySelector('input[id=date]').value); 
//         process.stdout.write("CURDATE: " + curdate + "\n");
//         // const input = await page.$('input[id=date]');
//         await page.focus('input[id=date]');  // input.click();
//         await page.keyboard.type("");
//         await page.keyboard.type(seldate);
//         // await page.$eval('input[id=date]', (el, seldate) => el.setAttribute("value", seldate), seldate);
//         process.stdout.write("DATE: " + seldate + "\n");
//    //     await page.evaluate(() => document.querySelector('input[id=date]').value = seldate); 
//    //     await page.$eval('input[id=date]', (e, seldate) => { 
//    //             e.setAttribute("value", seldate),
//    //         seldate
//    //        });
//         await delay(500);
//         const curdate2 = await page.evaluate(() => document.querySelector('input[id=date]').value); 
//         process.stdout.write("CURDATE2: " + curdate2 + "\n");
//        } catch (err) {
//            process.stdout.write("ERR3: " + err + "\n");
//        }
//      }
      // select timestep
      var num = "00";
      if (tstep === "false") {
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
      await graph.screenshot({ path: './tmp/' + seldate + '_' + curmodel + '_' + num + '.png' });

    });

    if (anim === "true") {
        for (let i=0; i<25; i++) {
            try {
                process.stdout.write("QUEUEING step:" + i + "\n");
                await cluster.queue([i, curmodel, seldate, variable]);
            } catch (err) {
                console.log(err);
                      process.stdout.write("ERROR:" + err + "\n");
            }
        }
    } else {
        process.stdout.write("QUEUEING current:" + anim + "\n");
        cluster.queue([anim, curmodel, seldate, variable]);
    }

    await cluster.idle();
    await cluster.close();
}

var anim = process.argv[2];      // default: false;
var curmodel = process.argv[3];  // default: "none";
var seldate = process.argv[4];   // default: "none";
var variable = process.argv[5];  // default: OD550_DUST

process.stdout.write("START -> ANIM: " + anim + " CURMODEL: " + curmodel + " DATE: " + seldate + " VAR: " +  variable + "\n");
RunCluster(anim, curmodel, seldate, variable);

