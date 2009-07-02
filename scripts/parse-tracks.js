/*Copyright (c) 2009 Johan Uhle

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
*/

var marker = new Object();
var html = new Object();

var SC = SC || {};
$.extend(SC, {
	
  parseTracks: function(url) {
		/*  This function takes a url to JSON data.
				It fetches the data and makes a bubble on the map for every track.
		*/
		$.getJSON(url,'',
			function(data) { 
				if ( data.length < 1) return false;
				
				$.each( data,	function( intIndex, objValue ) {
							point = new GPoint(objValue['location_lat'], objValue['location_lng']);
							marker[objValue['track_id']] = new GMarker(point);

							html[objValue['track_id']] = $('#bubble-template')
		            															.clone()
																	            .attr('id', 'bubble' + objValue['track_id']);
						  html[objValue['track_id']].find('.title').html(objValue['title']);
		          html[objValue['track_id']].find('.avatar').attr("src",objValue['avatar_url']);            
		          html[objValue['track_id']].find('ul li span.artist').html(objValue['username']);
		          html[objValue['track_id']].find('ul li span.time').html(objValue['created_minutes_ago'] + " minutes ago");
		          html[objValue['track_id']].find('ul li a.play-button').click(function(ev) {
																									$("#player-container").slideDown('slow');
																									if(window.soundManager.swfLoaded) window.soundManager.stopAll()
																									$('#player .sc-player').remove();																																	
																									$('<a class="soundcloud-player" href="'+objValue['permalink']+'">Play</a>').appendTo("#player");
																									$('#player .soundcloud-player').scPlayer({width:700, collapse:false, autoplay:true});
																									$('<img class="waveform" src="' + objValue['waveform_url'] + '" />').appendTo('#player .sc-player');
																									return false;
																								});

							GEvent.addListener(marker[objValue['track_id']], "click", function()
							      		 		{marker[objValue['track_id']].openInfoWindow(html[objValue['track_id']][0])});
							map.addOverlay(marker[objValue['track_id']]);					
					});
			}
		);
	},
	
	removeAllMarker: function() {
		
		$.each(marker, function( intIndex, objValue ) {			
			GEvent.clearInstanceListeners(marker[intIndex]);
			map.removeOverlay(marker[intIndex]);
			marker[intIndex] = null;
			html[intIndex] = null;
		});
		
		marker = new Object();
		html = new Object();
	}
	
});

$(function() {
	$('#link_all').click(function(ev) { SC.removeAllMarker(); SC.parseTracks('frontend-json/');});
	$('#link_rock').click(function(ev) { SC.removeAllMarker(); SC.parseTracks('frontend-json/rock');});
	$('#link_techno').click(function(ev) { SC.removeAllMarker(); SC.parseTracks('frontend-json/techno');});	
	$('#link_house').click(function(ev) { SC.removeAllMarker(); SC.parseTracks('frontend-json/house');});
	
	SC.parseTracks('frontend-json/');
});

