//
// uWiki.js (pronounced "micro-wiki")
//
// Adapted from showdown.js (http://www.attacklab.net/) by John Frasier
//
// Copyright (c) 2007 John Fraser.
//
// Redistributable under a BSD-style open source license.
//

//
// Register for onload
//
window.onload = startGui;


//
// Globals
//

var converter;
var convertTextTimer,processingTime;
var lastText,lastOutput;
var lastTab, activePane;
var convertTextSetting, convertTextButton;
var inputPane,previewPane,outputPane,syntaxPane,footer,display;
var maxDelay = 3000; // longest update pause (in ms)

//
//	Initialization
//

function startGui() {
  // find elements
  convertTextSetting = document.getElementById("convertTextSetting");
  convertTextButton = document.getElementById("convertTextButton");
  
  inputPane = document.getElementById("inputPane");
  previewPane = document.getElementById("previewPane");
  outputPane = document.getElementById("outputPane");
  syntaxPane = document.getElementById("syntaxPane");
  footer = document.getElementById("footer");
  display = document.getElementById("display");
  lastTab = document.getElementById("ptab");

  // set event handlers
  convertTextSetting.onchange = onConvertTextSettingChanged;
  convertTextButton.onclick = onConvertTextButtonClicked;
  window.onresize = setPaneHeights;
  
  // First, try registering for keyup events
  // (There's no harm in calling onInput() repeatedly)
  window.onkeyup = inputPane.onkeyup = onInput;
  
  // In case we can't capture paste events, poll for them
  var pollingFallback = window.setInterval(function(){
    if(inputPane.value != lastText)
      onInput();
  },1000);
  
  // Try registering for paste events
  inputPane.onpaste = function() {
    // It worked! Cancel paste polling.
    if (pollingFallback!=undefined) {
      window.clearInterval(pollingFallback);
      pollingFallback = undefined;
    }
    onInput();
  }
  
  // Try registering for input events (the best solution)
  if (inputPane.addEventListener) {
    // Let's assume input also fires on paste.
    // No need to cancel our keyup handlers;
    // they're basically free.
    inputPane.addEventListener("input",inputPane.onpaste,false);
  }
  
  // poll for changes in font size
  // this is cheap; do it often
  window.setInterval(setPaneHeights,250);
  
  // start with blank page?
    if (top.document.location.href.match(/\?blank=1$/))
      inputPane.value = "";
  
  // build the converter
  converter = new Showdown.converter();
  
  // do an initial conversion to avoid a hiccup
  convertText();
  
  // give the input pane focus
  inputPane.focus();
  
  // start the other panes at the top
  // (our smart scrolling moved them to the bottom)
  previewPane.scrollTop = 0;
  outputPane.scrollTop = 0;
  selectPane('previewPane');
}


//
//	Conversion
//

function convertText() {
  // get input text
  var text = inputPane.value;
  
  // if there's no change to input, cancel conversion
  if (text && text == lastText) {
    return;
  } else {
    lastText = text;
  }
  
  var startTime = new Date().getTime();
  
  // Do the conversion
  text = converter.makeHtml(text);
  
  // display processing time
  var endTime = new Date().getTime();	
  processingTime = endTime - startTime;
  document.getElementById("processingTime").innerHTML = processingTime+" ms";
  
  // save proportional scroll positions
  saveScrollPositions();
  
  // Update the appropriate pane
  lastOutput = text;
  updateActivePane()
  
  // restore proportional scroll positions
  restoreScrollPositions();
};


//
//	Event handlers
//

function onConvertTextSettingChanged() {
  // If the user just enabled automatic
  // updates, we'll do one now.
  onInput();
}

function onConvertTextButtonClicked() {
  // hack: force the converter to run
  lastText = "";
  
  convertText();
  inputPane.focus();
}

function onSubmit () {
  document.getElementById('html').value=converter.makeHtml(inputPane.value)
}

function selectTab(tab, pane){
  lastTab.className='';
  tab.className='selected';
  lastTab = tab;
  selectPane(pane);
}

function selectPane(pane) {
  previewPane.style.display = "none";
  outputPane.style.display = "none";
  syntaxPane.style.display = "none";
  
  // now make the selected one visible
  top[pane].style.display = "block";
  
  setPaneHeights();
  activePane = pane;
  updateActivePane();
}

function updateActivePane() {
  if (activePane == "outputPane") { outputPane.value = lastOutput; }
  else if (activePane == "previewPane") { previewPane.innerHTML = lastOutput; }
}

function onInput() {
  // In "delayed" mode, we do the conversion at pauses in input.
  // The pause is equal to the last runtime, so that slow
  // updates happen less frequently.
  //
  // Use a timer to schedule updates.  Each keystroke
  // resets the timer.
  
  // if we already have convertText scheduled, cancel it
  if (convertTextTimer) {
    window.clearTimeout(convertTextTimer);
    convertTextTimer = undefined;
  }
  
  if (convertTextSetting.value != "manual") {
    var timeUntilConvertText = 0;
    if (convertTextSetting.value == "delayed") {
      // make timer adaptive
      timeUntilConvertText = processingTime;
    }
    
    if (timeUntilConvertText > maxDelay)
      timeUntilConvertText = maxDelay;
    
    // Schedule convertText().
    // Even if we're updating every keystroke, use a timer at 0.
    // This gives the browser time to handle other events.
    convertTextTimer = window.setTimeout(convertText,timeUntilConvertText);
  }
}


//
// Smart scrollbar adjustment
//
// We need to make sure the user can't type off the bottom
// of the preview and output pages.  We'll do this by saving
// the proportional scroll positions before the update, and
// restoring them afterwards.
//

var previewScrollPos;
var outputScrollPos;

function getScrollPos(element) {
    // favor the bottom when the text first overflows the window
    if (element.scrollHeight <= element.clientHeight)
	return 1.0;
    return element.scrollTop/(element.scrollHeight-element.clientHeight);
}

function setScrollPos(element,pos) {
    element.scrollTop = (element.scrollHeight - element.clientHeight) * pos;
}

function saveScrollPositions() {
    previewScrollPos = getScrollPos(previewPane);
    outputScrollPos = getScrollPos(outputPane);
}

function restoreScrollPositions() {
    // hack for IE: setting scrollTop ensures scrollHeight
    // has been updated after a change in contents
    previewPane.scrollTop = previewPane.scrollTop;

    setScrollPos(previewPane,previewScrollPos);
    setScrollPos(outputPane,outputScrollPos);
}

//
// Textarea resizing
//
// Some browsers (i.e. IE) refuse to set textarea
// percentage heights in standards mode. (But other units?
// No problem.  Percentage widths? No problem.)
//
// So we'll do it in javascript.  If IE's behavior ever
// changes, we should remove this crap and do 100% textarea
// heights in CSS, because it makes resizing much smoother
// on other browsers.
//

function getTop(element) {
    var sum = element.offsetTop;
    while(element = element.offsetParent)
	sum += element.offsetTop;
    return sum;
}

function getElementHeight(element) {
    var height = element.clientHeight;
    if (!height) height = element.scrollHeight;
    return height;
}

function getWindowHeight(element) {
    if (window.innerHeight)
	return window.innerHeight;
    else if (document.documentElement && document.documentElement.clientHeight)
	return document.documentElement.clientHeight;
    else if (document.body)
	return document.body.clientHeight;
}

function setPaneHeights() {
    var footerBottom = getTop(footer) + getElementHeight(footer);
    var windowHeight = getWindowHeight();
    var adjustment = windowHeight-footerBottom;
    if (adjustment==0) { return; }
    var newSize = getElementHeight(display) + adjustment - 10;
    if (newSize<50) { return; }
    newSize = newSize+"px";
    inputPane.style.height = newSize;
    previewPane.style.height = newSize;
    outputPane.style.height = newSize;
    syntaxPane.style.height = newSize;
}