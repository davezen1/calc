/* global jQuery, document, window */

import 'document-register-element';

import * as supports from './feature-detection';

import { dispatchBubbly } from './custom-event';

const $ = jQuery;

const VALIDITY_CHECK_INTERVAL = 250;

const MISC_ERROR = 'Sorry, we’re having trouble. ' +
                   'Please try again later or refresh your browser.';

let delegate = {
  redirect(url) {
    window.location = url;
  },
  alert(msg) {
    // TODO: Be more user-friendly here.
    window.alert(msg);   // eslint-disable-line no-alert
  },
};

function replaceForm(form, html) {
  const newForm = $(html)[0];

  // Replace the form and bind it.
  $(form).replaceWith(newForm);

  // Animate the new form so the user notices it.
  // TODO: Consider using a CSS class w/ a transition or animation instead.
  $(newForm).hide().fadeIn();
}

function populateFormData(form, formData) {
  // IE11 doesn't support FormData.prototype.delete(), so we need to
  // manually construct the FormData ourselves (we used to have
  // the browser construct it for us, and then replace the file).
  for (let i = 0; i < form.elements.length; i++) {
    const el = form.elements[i];

    if (el.isUpgraded) {
      formData.append(el.name, el.upgradedValue);
    } else if (el.type === 'radio' || el.type === 'checked') {
      // https://github.com/18F/calc/issues/570
      throw new Error(`unsupported input type: ${el.type}`);
    } else if (el.type === 'file') {
      for (let j = 0; j < el.files.length; j++) {
        formData.append(el.name, el.files[j]);
      }
    } else {
      formData.append(el.name, el.value);
    }
  }

  return formData;
}

function willValidate(form) {
  for (let i = 0; i < form.elements.length; i++) {
    const el = form.elements[i];

    if (el.type !== 'hidden' && !el.checkValidity()) {
      return false;
    }
  }

  return true;
}

function disableSubmitIfInvalid(form) {
  const $submit = $('button[type=submit]', form);

  $submit.prop('disabled', !willValidate(form));
}

function bindForm(form) {
  $(form).on('submit', (e) => {
    if (form.isDegraded) {
      // Assume the browser has
      // minimal HTML5 support and just let the user submit the form manually.
    } else {
      e.preventDefault();

      const formData = new window.FormData();

      populateFormData(form, formData);

      const req = $.ajax(form.action, {
        processData: false,
        contentType: false,
        data: formData,
        method: form.method,
      });

      $(form).addClass('submit-in-progress');

      req.done((data) => {
        if (data.form_html) {
          replaceForm(form, data.form_html);
        } else if (data.redirect_url) {
          delegate.redirect(data.redirect_url);
        } else {
          delegate.alert(MISC_ERROR);
          $(form).removeClass('submit-in-progress');
        }
      });

      req.fail(() => {
        delegate.alert(MISC_ERROR);
        $(form).removeClass('submit-in-progress');
      });
    }
  });
}

exports.setDelegate = newDelegate => {
  delegate = newDelegate;
  return delegate;
};
exports.MISC_ERROR = MISC_ERROR;
exports.bindForm = bindForm;
exports.populateFormData = populateFormData;

window.testingExports__ajaxform = exports;

class AjaxForm extends window.HTMLFormElement {
  createdCallback() {
    this.isDegraded = !supports.formData() ||
                      supports.isForciblyDegraded(this);
    bindForm(this);
    dispatchBubbly(this, 'ajaxformready');
  }

  attachedCallback() {
    if (!this.isDegraded && supports.formValidation()) {
      const updateValidity = disableSubmitIfInvalid.bind(null, this);

      this._validityCheckInterval = window.setInterval(
        updateValidity,
        VALIDITY_CHECK_INTERVAL
      );
    }
  }

  detachedCallback() {
    window.clearInterval(this._validityCheckInterval);
  }
}

document.registerElement('ajax-form', {
  extends: 'form',
  prototype: AjaxForm.prototype,
});
