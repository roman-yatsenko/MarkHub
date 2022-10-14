// https://overcoder.net/q/30481/%D0%BA%D0%BE%D0%BD%D0%B2%D0%B5%D1%80%D1%82%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D1%82%D1%8C-%D0%B4%D0%B0%D1%82%D1%83-%D0%B2-%D0%B4%D1%80%D1%83%D0%B3%D0%BE%D0%B9-%D1%87%D0%B0%D1%81%D0%BE%D0%B2%D0%BE%D0%B9-%D0%BF%D0%BE%D1%8F%D1%81-%D0%B2-javascript
// https://docs.djangoproject.com/en/4.1/ref/templates/builtins/#date
// https://momentjs.com/timezone/

function toTimeZone(time, zone) {
    var format = 'YYYY/MM/DD HH:mm:ss ZZ';
    return moment(time, format).tz(zone).format(format);
}
