/* global $, window, document */

// The following feature detectors are ultimately pulled from Modernizr.

module.exports = {
  dragAndDrop() {
    const div = document.createElement('div');
    return ('draggable' in div) || ('ondragstart' in div && 'ondrop' in div);
  },

  formData() {
    return 'FormData' in window;
  },

  dataTransfer() {
    // Browsers that support FileReader support DataTransfer too.
    return 'FileReader' in window;
  },

  formValidation() {
    // http://stackoverflow.com/a/8550926
    const input = document.createElement('input');
    return typeof input.checkValidity === 'function';
  },

  // We'd like to make it possible to forcibly degrade components that have
  // a `data-force-degradation` attribute on them or one of their
  // ancestors. This makes it easier to test degraded functionality and
  // also allows us to (potentially) provide a "safe mode" that users
  // who are experiencing browser compatibility issues can opt into.

  isForciblyDegraded(el) {
    return !!$(el).closest('[data-force-degradation]').length;
  },
};
