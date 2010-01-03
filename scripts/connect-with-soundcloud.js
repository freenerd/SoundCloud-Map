var SC = {
  'Connect': {
    'prepareButton': function(link,options){
      SC.Connect.wrapped_callback = options.callback;
      link.click(function(){
        SC.Connect.popup_window = SC.Connect.open_login(options);
        return false;
      });
    },
    'callback': function(query_obj){
      SC.Connect.popup_window.close();
      SC.Connect.wrapped_callback(query_obj);
    },
    
    'open_login': function(options){
      
      var pLeft = (document.all)?window.screenLeft:window.screenX;
      var pTop = (document.all)?window.screenTop:window.screenY;
      
      var pXCenter = pTop + (window.outerHeight/2);
      var pYCenter = pLeft + (window.outerWidth/2);
          
      var width = 456;
      var height = 550;
      
      var top = pXCenter - (height/2);
      var left = pYCenter - (width/2);
 
      var params = 'width='+width+', height='+height;
      params += ', top='+top+', left='+left;
      params += "location=1, toolbar=no,scrollbars=yes"
      return window.open(options.request_token_endpoint,"sc_connect_popup",params);
    }
  },
  'QueryToObject': function(query) {
    var obj = {};
    var splitted_url =document.URL.split("?");
    var query = splitted_url[1] ? splitted_url[1] : "";
    var vars = query.split("&");
    for (var i=0;i<vars.length;i++) {
      var pair = vars[i].split("=");
      obj[pair[0]] = decodeURIComponent(pair[1]);
    }
    return(obj);
  }
};