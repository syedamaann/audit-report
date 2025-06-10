const fs = require('fs');
const path = require('path');
const express = require('express');
const EmlParser = require('eml-parser');

const app = express();

// Parse .eml and return complete JSON data
app.get('/email/json', async (req, res) => {
  const filePath = path.join(__dirname, 'No_6742550656454.eml');
  const parser = new EmlParser(fs.createReadStream(filePath));
  try {
    const result = await parser.parseEml();
    res.json(result);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Error parsing .eml' });
  }
});

// Parse .eml and serve HTML with inline images
app.get('/email', async (req, res) => {
  const filePath = path.join(__dirname, 'No_6742550656454.eml');
  const parser = new EmlParser(fs.createReadStream(filePath));
  try {
    const result = await parser.parseEml();

    let html = result.html || result.textAsHtml || '<body><pre>' + result.text + '</pre></body>';

    // Inline all inline attachments via data: URIs
    (result.attachments || []).forEach(att => {
      if (att.inline && att.cid) {
        const mime = att.contentType || att.mimeType;
        const b64 = att.content.toString('base64');
        const dataUri = `data:${mime};base64,${b64}`;
        html = html.replace(new RegExp(`cid:${att.cid}`, 'g'), dataUri);
      }
    });

    res.send(`
      <!DOCTYPE html>
      <html>
        <head><meta charset="utf-8"><title>${result.subject}</title></head>
        <body>${html}</body>
      </html>
    `);
  } catch (err) {
    console.error(err);
    res.status(500).send('Error parsing .eml');
  }
});

// Serve static files
app.use(express.static(path.join(__dirname, 'public')));

app.listen(3003, () => console.log('Server running on http://localhost:3000'));
