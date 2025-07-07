(async function() {
  function sendStatus(text) {
    chrome.runtime.sendMessage({type: 'autofill-status', text});
  }
  try {
    sendStatus('🤖 Scanning form fields...');
    const API_BASE = 'http://localhost:8000';
    const USER_ID = '550e8400-e29b-41d4-a716-446655440000';
    function detectFieldType(element) {
      const text = ((element.name || '') + (element.id || '') + (element.placeholder || '') + (element.labels?.[0]?.textContent || '')).toLowerCase();
      if (element.type === 'email' || text.includes('email')) return 'email';
      if (element.type === 'tel' || text.includes('phone') || text.includes('tel')) return 'phone';
      if (text.includes('first') && text.includes('name')) return 'first_name';
      if (text.includes('last') && text.includes('name')) return 'last_name';
      if (text.includes('name') && !text.includes('user') && !text.includes('company')) return 'full_name';
      if (text.includes('address') || text.includes('street')) return 'address';
      if (text.includes('city')) return 'city';
      if (text.includes('state') || text.includes('province')) return 'state';
      if (text.includes('zip') || text.includes('postal')) return 'zip_code';
      if (text.includes('linkedin')) return 'linkedin';
      if (text.includes('github')) return 'github';
      if (text.includes('website') || text.includes('portfolio')) return 'website';
      if (element.tagName === 'TEXTAREA' || text.includes('cover') || text.includes('letter')) return 'cover_letter';
      if (text.includes('skill')) return 'skills';
      if (text.includes('experience')) return 'experience';
      if (text.includes('education')) return 'education';
      return 'text';
    }
    function getFieldLabel(element) {
      if (element.labels && element.labels[0]) return element.labels[0].textContent.trim();
      const closest = element.closest('label');
      if (closest) return closest.textContent.replace(element.value || '', '').trim();
      const prev = element.previousElementSibling;
      if (prev && ['LABEL', 'SPAN', 'DIV', 'P'].includes(prev.tagName)) {
        const text = prev.textContent.trim();
        if (text.length < 100) return text;
      }
      return element.placeholder || element.name || 'Field';
    }
    // Find form fields
    const fields = Array.from(document.querySelectorAll('input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="file"]), textarea, select'))
      .filter(el => el.offsetParent !== null)
      .map(el => ({
        element: el,
        name: el.name || el.id || 'field_' + Date.now(),
        label: getFieldLabel(el),
        type: detectFieldType(el),
        context: el.placeholder || ''
      }));
    if (fields.length === 0) {
      sendStatus('❌ No form fields found');
      return;
    }
    sendStatus('🔍 Found ' + fields.length + ' fields. Getting your data...');
    // Prepare fields for API
    const apiFields = fields.map(f => ({
      name: f.name,
      label: f.label,
      type: f.type,
      context: f.context
    }));
    // Call field matching API
    const response = await fetch(API_BASE + '/api/match-fields-bulk', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': USER_ID
      },
      body: JSON.stringify({
        fields: apiFields,
        user_id: USER_ID
      })
    });
    if (!response.ok) {
      sendStatus('❌ API error: ' + response.status);
      return;
    }
    const result = await response.json();
    const matches = result.matched_fields;
    // Fill form fields
    let filled = 0;
    for (const field of fields) {
      const match = matches[field.name];
      if (match && match.matched && match.confidence > 0.3) {
        try {
          if (field.element.tagName === 'SELECT') {
            const option = Array.from(field.element.options).find(opt =>
              opt.text.toLowerCase().includes(match.value.toLowerCase()) ||
              opt.value.toLowerCase().includes(match.value.toLowerCase())
            );
            if (option) {
              field.element.value = option.value;
              filled++;
            }
          } else {
            field.element.value = match.value;
            field.element.dispatchEvent(new Event('input', {bubbles: true}));
            field.element.dispatchEvent(new Event('change', {bubbles: true}));
            filled++;
          }
        } catch (err) {
          // ignore
        }
      }
    }
    sendStatus('✅ Autofill Complete! Filled ' + filled + ' of ' + fields.length + ' fields.');
  } catch (e) {
    sendStatus('❌ Error: ' + (e.message || e));
  }
})(); 