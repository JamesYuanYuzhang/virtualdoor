//To Do: Add Visibility toggle  
var url="https://vyem34kxsa.execute-api.us-east-1.amazonaws.com/v1/virtualdoor/passcode"
var apigClient = apigClientFactory.newClient();
var text = document.getElementById("text");
var body = {
  // This is where you define the body of the request,
};


const inputs = document.querySelectorAll('.passcode-area input');
//return all the elements of that area
inputs[0].focus();
for (elem of inputs) {
  elem.addEventListener('input', function() {
    const value = this.value;
    const nextElement = this.nextElementSibling;
    if (value === '' || !nextElement) {
      return;
    }
    nextElement.focus();
  });
}
for (let elem of inputs) {
  elem.addEventListener('keydown', function(event) {
     //Right Arrow Key
    if (event.keyCode == 39) {
      this.nextElementSibling.focus();
    }
     //Left Arrow Key
    //Add Highlight
    if (event.keyCode == 37) {
      this.previousElementSibling.focus();
    }
    //Backspace Key
    if (event.keyCode == 8 && event.metaKey) {
      console.log('🐰🥚 FOUND!!! Cmd + Backspace = clear all');
      for (innerElem of inputs) {
        innerElem.value = '';
      }
      inputs[0].focus();
    } else if (event.keyCode == 8) {
      if(elem.value === '') {
        this.previousElementSibling.focus();
        return;
      }
      elem.value = '';
    }
  });
}

$('.submitBtn').click(function() {
  submitForm();
});


function submitForm() {
  var otp = $("#t1").val()+$("#t2").val()+$("#t3").val()+$("#t4").val()+$("#t5").val()+$("#t6").val();
  body["otp"]=otp;
  //var data = {"otp":otp};
  console.log(body);
  apigClient.virtualdoorPasscodePost(null, body)
  .then(function(result){
      console.log("success");
      console.log(result);
      //document.write("<img src='./check.png'>");
      //self.location='./webpage1_success.html';
      text.innerHTML =result.data["body"];
    }).catch( function(result){
      console.log("failed");
      console.log(result);
    });



  // $.ajax({
  //   type: "POST",
  //   url: url,
  //   crossDomain: true,
  //   data: data,
  //   dataType: "jsonp",
  //   jsonpCallback :'callbackdata',
  //   //async:false,
  //   success: function(response){
  //     console.log("success");
  //     name = response.name;
  //     showAlert("alert-success", "Welcome, " + name + "!");
  //   },
  //   error: function(xhr, status, error){
  //     console.log("Failed");
  //     console.log(xhr);
  //     console.log(status);
  //     console.log(error);
  //     console.log(xhr.responseText);
  //     errMsg = "Failed.<br>" + xhr.responseText;
  //     showAlert("alert-danger", errMsg);
  //   }
  // });
}


// type: the alert type of bootstrap.
// function showAlert(type, msg) {
//   $("#formAlert").remove();

//   date = new Date();
//   time = date.toLocaleTimeString();
//   newElement = 
//     "<div id='formAlert' class='alert top-1 " + type + "' role='alert'>" +
//     time + "<br>" + msg +
//     "</div>";
//   $("#alertCol").append(newElement);

// }