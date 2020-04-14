function dynamicallyLoadScript(url) {
    var script = document.createElement("script");  // create a script DOM node
    script.src = url;  // set its src to the provided URL
    document.head.appendChild(script);  // add it to the end of the head section of the page (could change 'head' to 'body' to add it to the end of the body section instead)
}
// var apigClient;


// $(window).load(function() {
//   dynamicallyLoadScript("apiGateway-js-sdk/apigClient.js");
//   dynamicallyLoadScript("apiGateway-js-sdk/aws-sdk-min.js");
//   apigClient = apigClientFactory.newClient();
// });

var valid 
var lastName
var firstName
var phone
// var imgUrl = "https://gate-unknown-faces.s3.amazonaws.com/unknown.jpg";
// var ForReading=1; 
// var src = 'https://virtualdoor.s3-us-west-2.amazonaws.com/faceid.txt'
// var fso=new ActiveXObject("Scripting.FileSystemObject"); 
// var f=fso.OpenTextFile(src,ForReading); 
// var face_id = f.readAll()
var face_id
$('.btn').click(function() {
  var apigClient = apigClientFactory.newClient();
  console.log(2)
  firstName = document.getElementById('inputFirstName').value;
  lastName = document.getElementById('inputLastName').value;
  phone = document.getElementById('inputPhone').value;
  // var reader = new FileReader();
  // faceid = reader.readAsText('https://virtualdoor.s3-us-west-2.amazonaws.com/faceid.txt')
  // reader.οnlοad=function(e)
  // {
  //   var result=document.getElementById("result");
  //   result.innerHTML=this.result;
  // }
  if ($.trim(firstName) == '') {
  	alert("no first name")
  	self.location='./webpage1.html'
    return false;
	}
  else if ($.trim(lastName) == '') {
  	alert("no last name")
  	self.location='./webpage1.html'
    return false;
  }
  else if ($.trim(phone) == '') {
  	alert("no email")
  	self.location='./webpage1.html'
    return false;
  }
  var name =firstName.toLowerCase() + "_" + lastName.toLowerCase();
  var body = {
                "name" : name,
                // "faceid" : faceid,
                "email" : phone    
  };
  console.log(body);
  apigClient.virtualdoorSubmitPost({}, body, {})
      .then(function(result){
        // Add success callback code here
        console.log(result);
        self.location='./webpage1_success.html';
          
        
      }).catch( function(result){
        // Add error callback code here.
        console.log("failded");

      });
        
  
});