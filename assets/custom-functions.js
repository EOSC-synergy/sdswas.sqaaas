window.forecastTab = Object.assign({}, window.forecastTab, {  
    forecastMaps: {  
        styleHandle: function(feature, context){
            // get props from hideout
	    const {bounds, colorscale, style, colorProp} = context.props.hideout;
            // get value the determines the color
            const value = feature.properties[colorProp];
	    for (let i = 0; i < bounds.length; ++i) {
		if (value > bounds[i]) {
	            // set the fill color according to the class
		    style.fillColor = colorscale[i];
		}
	    }
            return style;
        },
	pointToLayer: function(feature, latlng, context){
            const {min, max, colorscale, circleOptions, colorProp} = context.props.hideout;
            // set color based on color prop.
            circleOptions.fillColor = feature.properties[colorProp];
            // sender a simple circle marker.
            return L.circleMarker(latlng, circleOptions);
        },
	bindTooltip: function(feature, layer, context) {
            const props = feature.properties;
            // delete props.cluster;
            layer.bindTooltip(JSON.stringify(props.value), { opacity: 1.0 })
        }
    }
});

window.evaluationTab = Object.assign({}, window.evaluationTab, {  
    evaluationMaps: {  
	pointToLayer: function(feature, latlng, context){
            const {circleOptions} = context.props.hideout;
            // sender a simple circle marker.
            return L.circleMarker(latlng, circleOptions);
        },
    }
});

window.observationsTab = Object.assign({}, window.observationsTab, {  
    observationsMaps: {  
	pointToLayer: function(feature, latlng, context){
            const {colorscale, circleOptions, colorProp} = context.props.hideout;
            const value = feature.properties[colorProp];
            circleOptions.fillColor = colorscale[value];
            // sender a simple circle marker.
            return L.circleMarker(latlng, circleOptions);
        },
    }
});
