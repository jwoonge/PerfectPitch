/*!
    * Start Bootstrap - Creative v6.0.1 (https://startbootstrap.com/themes/creative)
    * Copyright 2013-2020 Start Bootstrap
    * Licensed under MIT (https://github.com/BlackrockDigital/startbootstrap-creative/blob/master/LICENSE)
    */
    (function($) {
  "use strict"; // Start of use strict

  // Smooth scrolling using jQuery easing
  $('a.js-scroll-trigger[href*="#"]:not([href="#"])').click(function() {
    if (location.pathname.replace(/^\//, '') == this.pathname.replace(/^\//, '') && location.hostname == this.hostname) {
      var target = $(this.hash);
      target = target.length ? target : $('[name=' + this.hash.slice(1) + ']');
      if (target.length) {
        $('html, body').animate({
          scrollTop: (target.offset().top - 72)
        }, 1000, "easeInOutExpo");
        return false;
      }
    }
  });

  // Closes responsive menu when a scroll trigger link is clicked
  $('.js-scroll-trigger').click(function() {
    $('.navbar-collapse').collapse('hide');
  });

  // Activate scrollspy to add active class to navbar items on scroll
  $('body').scrollspy({
    target: '#mainNav',
    offset: 75
  });

  // Collapse Navbar
  var navbarCollapse = function() {
    if ($("#mainNav").offset().top > 100) {
      $("#mainNav").addClass("navbar-scrolled");
    } else {
      $("#mainNav").removeClass("navbar-scrolled");
    }
  };
  // Collapse now if page is not at top
  navbarCollapse();
  // Collapse the navbar when page is scrolled
  $(window).scroll(navbarCollapse);

  // Magnific popup calls
  $('#portfolio').magnificPopup({
    delegate: 'a',
    type: 'image',
    tLoading: 'Loading image #%curr%...',
    mainClass: 'mfp-img-mobile',
    gallery: {
      enabled: true,
      navigateByImgClick: true,
      preload: [0, 1]
    },
    image: {
      tError: '<a href="%url%">The image #%curr%</a> could not be loaded.'
    }
  });

})(jQuery); // End of use strict

$("#upload_file_btn").click(function javascript_onclick(){
$("#upload_link").hide();
$("#upload_file").show();
});

$("#upload_link_btn").click(function javascript_onclick(){
$('#upload_file').hide();
$("#upload_link").show();

});

$("#show_pdf").click(function javascript_onclick(){

$("#results").show();
$("#home_btn").show();
var user_raw=new String(getip());
var user_name = user_raw.replace(/\./gi,'');
var user_name_form = {
  'user' : user_name
};
var formData = new FormData();
formData.append('name',user_name)
$.ajax({
  type: "POST",
  url: "upload/showpdf",
  data: formData,
  processData: false,
  contentType: false,
  cache: false,
  xhrFields: {
    responseType : 'arraybuffer'
  },
  timeout: 600000,
  success : function(response)
  {


     
    var options = {
      pdfOpenParams: {
          navpanes: 0,
          toolbar: 0,
          statusbar: 0,
          view:"FitV",
          pagemode:"thumbs",
          page: 1
      },
      forcePDFJS: true,
      PDFJS_URL:"../static/js/pdfjs/web/viewer.html"
    }

    var file = new Blob([response],{type : 'application/pdf'});
    const fileURL = window.URL.createObjectURL(file);
    var myPDF = PDFObject.embed(fileURL,"#pdf", options);
    
    var el = document.querySelector("#results");
    el.setAttribute("class", (myPDF) ?"success" :"fail");
    window.open(fileURL);
    $("#show_pd").hide();

     
    
    


  }

});



});


$("#show_pdf_link").click(function javascript_onclick(){

$("#results").show();
$("#home_btn").show();
var user_raw=new String(getip());
var user_name = user_raw.replace(/\./gi,'');
var user_name_form = {
  'user' : user_name
};
var formData = new FormData();
formData.append('name',user_name)
$.ajax({
  type: "POST",
  url: "youtube/showpdf",
  data: formData,
  processData: false,
  contentType: false,
  cache: false,
  xhrFields: {
    responseType : 'arraybuffer'
  },
  timeout: 600000,
  success : function(response)
  {



    var options = {
      pdfOpenParams: {
          navpanes: 0,
          toolbar: 0,
          statusbar: 0,
          view:"FitV",
          pagemode:"thumbs",
          page: 1
      },
      forcePDFJS: true,
      PDFJS_URL:"../static/js/pdfjs/web/viewer.html"
    }

    var file = new Blob([response],{type : 'application/pdf'});
    const fileURL = window.URL.createObjectURL(file);

    var myPDF = PDFObject.embed(fileURL,"#pdf", options);
    window.open(fileURL)
    var el = document.querySelector("#results");
    el.setAttribute("class", (myPDF) ?"success" :"fail");
    $("#show_pdf_link").hide();






  }

});



});


$("#home_btn").click(function javascript_onclick(){

  $("#results").hide();
  $("#home_btn").hide();
  $("#play_audio").hide();
  $("#player").hide()
  $("#show_pdf_link").hide();
  $("#show_pdf").hide();
  $("#upload_link_btn").show();
  $("#upload_file_btn").show();
  location.reload();
  
  
  
  });
function hide_form(){

  $("#upload_link").hide();
  $('#upload_file').hide();



}


/**
 * Get the user IP throught the webkitRTCPeerConnection
 * @param onNewIP {Function} listener function to expose the IP locally
 * @return undefined
 */
function getUserIP(onNewIP) { //  onNewIp - your listener function for new IPs
  //compatibility for firefox and chrome
  var myPeerConnection = window.RTCPeerConnection || window.mozRTCPeerConnection || window.webkitRTCPeerConnection;
  var pc = new myPeerConnection({
      iceServers: []
  }),
  noop = function() {},
  localIPs = {},
  ipRegex = /([0-9]{1,3}(\.[0-9]{1,3}){3}|[a-f0-9]{1,4}(:[a-f0-9]{1,4}){7})/g,
  key;

  function iterateIP(ip) {
      if (!localIPs[ip]) onNewIP(ip);
      localIPs[ip] = true;
  }

   //create a bogus data channel
  pc.createDataChannel("");

  // create offer and set local description
  pc.createOffer().then(function(sdp) {
      sdp.sdp.split('\n').forEach(function(line) {
          if (line.indexOf('candidate') < 0) return;
          line.match(ipRegex).forEach(iterateIP);
      });
      
      pc.setLocalDescription(sdp, noop, noop);
  }).catch(function(reason) {
      // An error occurred, so handle the failure to connect
  });

  //listen for candidate events
  pc.onicecandidate = function(ice) {
      if (!ice || !ice.candidate || !ice.candidate.candidate || !ice.candidate.candidate.match(ipRegex)) return;
      ice.candidate.candidate.match(ipRegex).forEach(iterateIP);
  };
}

// Usage

getUserIP(function(ip){
  document.getElementById("ip").innerHTML = 'Got your IP ! : '  + ip + " | verify in http://www.whatismypublicip.com/";
});


$("#link_finish").click(function (event) {

  //preventDefault 는 기본으로 정의된 이벤트를 작동하지 못하게 하는 메서드이다. submit을 막음
  event.preventDefault();

  // Get form
  var form = $('#upload_link')[0];

// Create an FormData object 
  var data = new FormData(form);
  var user_raw=new String(getip());
  var user_name = user_raw.replace(/\./gi,'');
  data.append('name',user_name)
  hide_form();
// disabled the submit button
  $("#link_finish").prop("disabled", true);
  $("#upload_link_btn").hide();
  $("#upload_file_btn").hide();
  $("#progress_notice").show();
  $("#progress_notice2").show();
  $("#progress").show();

  $.ajax({
      type: "POST",
      enctype: 'multipart/form-data',
      url: "youtube/translate_youtube_link",
      data: data,
      processData: false,
      contentType: false,
      cache: false,
      xhrFields: {
        responseType : 'blob'
      },
      timeout: 600000,
      success : function(response)
      {
    
    
          $("#progress_notice").hide();
          $("#progress_notice2").hide();
          $("#show_pdf_link").show()
          $("#play_audio").show()
          //$("#play_pdf").show()
          var blob=new Blob([response]);

          var link=document.createElement('a');
          link.href=window.URL.createObjectURL(blob);
          //link.href="youtube/translate_youtube_link";



          link.download="OUTPUT.pdf";
          link.click();
          //location.href = "youtube/translate_youtube_link";
          //location.download = 'file.mid';
          //location.click();
          $("#progress").hide();
          alert("Finish!");
          $("#link_finish").prop("disabled", false);
         
        
    

         
        
        

    
      },
      error:function(request,status,error){
        alert("code:"+request.status+"\n"+"message:"+'Incorrect Youtube Link'+"\n");
        location.reload();
       }
  });



});

$("#upload_finish").click(function (event) {

  //preventDefault 는 기본으로 정의된 이벤트를 작동하지 못하게 하는 메서드이다. submit을 막음
  event.preventDefault();

  // Get form
  var form = $('#upload_file')[0];


// Create an FormData object 
  var data = new FormData(form);
  var user_raw=new String(getip());
  var user_name = user_raw.replace(/\./gi,'');
  data.append('name',user_name)
  hide_form();
// disabled the submit button
  $("#link_finish").prop("disabled", true);
  $("#upload_link_btn").hide();
  $("#upload_file_btn").hide();
  $("#progress_notice").show();
  $("#progress_notice2").show();
  $("#progress").show();

  $.ajax({
      type: "POST",
      enctype: 'multipart/form-data',
      url: "upload/upload",
      data: data,
      processData: false,
      contentType: false,
      cache: false,
      xhrFields: {
        responseType : 'blob'
      },
      timeout: 600000,
      success : function(response)
      {
    
    
          $("#progress_notice").hide();
          $("#progress_notice2").hide();
          $("#show_pdf").show()
          $("#play_audio").show()
          var blob=new Blob([response]);
          var link=document.createElement('a');
          link.href=window.URL.createObjectURL(blob);
          //link.href="youtube/translate_youtube_link";
          link.download="OUTPUT.pdf";
          link.click();
          //location.href = "youtube/translate_youtube_link";
          //location.download = 'file.mid';
          //location.click();
          $("#progress").hide();
          alert("Finish!");
          $("#link_finish").prop("disabled", false);
         
        
    

         
        
        

    
      },
      error:function(request,status,error){
        alert("code:"+request.status+"\n"+"message:"+'Ivalid File'+"\n");
        location.reload();
       }
  });



});
$("#show_pdf").click(function javascript_onclick(){

$("#results").show();
$("#home_btn").show();
var user_raw=new String(getip());
var user_name = user_raw.replace(/\./gi,'');
var user_name_form = {
  'user' : user_name
};
var formData = new FormData();
formData.append('name',user_name)
$.ajax({
  type: "POST",
  url: "upload/showpdf",
  data: formData,
  processData: false,
  contentType: false,
  cache: false,
  xhrFields: {
    responseType : 'arraybuffer'
  },
  timeout: 600000,
  success : function(response)
  {



    var options = {
      pdfOpenParams: {
          navpanes: 0,
          toolbar: 0,
          statusbar: 0,
          view:"FitV",
          pagemode:"thumbs",
          page: 1
      },
      forcePDFJS: true,
      PDFJS_URL:"../static/js/pdfjs/web/viewer.html"
    }

    var file = new Blob([response],{type : 'application/pdf'});
    const fileURL = window.URL.createObjectURL(file);
    var myPDF = PDFObject.embed(fileURL,"#pdf", options);

    var el = document.querySelector("#results");
    el.setAttribute("class", (myPDF) ?"success" :"fail");
    window.open(fileURL);
    $("#show_pdf").hide();






  }

});



});

$("#play_audio").click(function javascript_onclick(){

$("#player").show();
$("#home_btn").show();
var user_raw=new String(getip());
var user_name = user_raw.replace(/\./gi,'');
var user_name_form = {
  'user' : user_name
};
var formData = new FormData();
formData.append('name',user_name)

 $.ajax({
  type: "POST",
  url: "youtube/playaudio",
  data: formData,
  processData: false,
  contentType: false,
  cache: false,
  xhrFields: {
    responseType : 'blob'
  },
  timeout: 600000,
        success: function( response ) {

            var file = new Blob([response]);
            var audio = new window.Audio();
            audio.src=window.URL.createObjectURL(file)

            $('audio #source').attr('src', audio.src);
            //var audio = $("#player")[0];
            //audio.play();
            $('audio').get(0).load();
            console.log("Finish Loading");
            console.log(audio.src);
            $('audio').get(0).play();
            $("#play_audio").hide();

        }






});
});