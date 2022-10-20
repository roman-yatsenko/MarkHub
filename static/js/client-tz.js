(function () {
  let dateTimeElement = document.getElementById("last-update");
  if (dateTimeElement) {
    const inputFormat = 'YYYY/MM/DD HH:mm:ss ZZ';
    const outputFormat = 'YYYY/MM/DD HH:mm:ss [GMT] Z';
    const zone = moment.tz.guess();
    dateTimeElement.innerText = moment(dateTimeElement.innerText, inputFormat).tz(zone).format(outputFormat);
  }
  })();
