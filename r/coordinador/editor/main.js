/**
 *  CKEditor 5 –  Builder configuration (no cambies nada de aquí salvo lo indicado).
 *  https://ckeditor.com/ckeditor-5/builder/
 */

/* -----------------------------------------------------------------
   1️⃣  IMPORTAR los módulos que el Builder generó
   ----------------------------------------------------------------- */
const {
    DecoupledEditor,
    Alignment,
    Autoformat,
    AutoImage,
    AutoLink,
    Autosave,
    BalloonToolbar,
    Base64UploadAdapter,
    BlockQuote,
    Bold,
    Bookmark,
    Code,
    CodeBlock,
    Emoji,
    Essentials,
    FindAndReplace,
    FontBackgroundColor,
    FontColor,
    FontFamily,
    FontSize,
    Fullscreen,
    GeneralHtmlSupport,
    Heading,
    HorizontalLine,
    HtmlComment,
    HtmlEmbed,
    ImageBlock,
    ImageCaption,
    ImageEditing,
    ImageInline,
    ImageInsert,
    ImageInsertViaUrl,
    ImageResize,
    ImageStyle,
    ImageTextAlternative,
    ImageToolbar,
    ImageUpload,
    ImageUtils,
    Indent,
    IndentBlock,
    Italic,
    Link,
    List,
    ListProperties,
    Markdown,
    MediaEmbed,
    Mention,
    Minimap,
    PageBreak,
    Paragraph,
    PasteFromMarkdownExperimental,
    PasteFromOffice,
    RemoveFormat,
    ShowBlocks,
    SpecialCharacters,
    SpecialCharactersArrows,
    SpecialCharactersCurrency,
    SpecialCharactersEssentials,
    SpecialCharactersLatin,
    SpecialCharactersMathematical,
    SpecialCharactersText,
    Strikethrough,
    Subscript,
    Superscript,
    Table,
    TableCaption,
    TableCellProperties,
    TableColumnResize,
    TableProperties,
    TableToolbar,
    TextPartLanguage,
    TextTransformation,
    Title,
    TodoList,
    Underline,
    WordCount
} = window.CKEDITOR;

/* -----------------------------------------------------------------
   2️⃣  LICENCIA y configuración (se mantiene tal cual)
   ----------------------------------------------------------------- */
const LICENSE_KEY =
    'eyJhbGciOiJFUzI1NiJ9.eyJleHAiOjE3NTcwMzAzOTksImp0aSI6ImJjMzI3ZmRhLTczYmItNDU1NC1iYWJlLTc1NGZlNmNkYzdiNSIsInVzYWdlRW5kcG9pbnQiOiJodHRwczovL3Byb3h5LWV2ZW50LmNrZWRpdG9yLmNvbSIsImRpc3RyaWJ1dGlvbkNoYW5uZWwiOlsiY2xvdWQiLCJkcnVwYWwiLCJzaCJdLCJ3aGl0ZUxhYmVsIjp0cnVlLCJsaWNlbnNlVHlwZSI6InRyaWFsIiwiZmVhdHVyZXMiOlsiKiJdLCJ2YyI6IjFhNzc3MWI4In0.hpqTUpyB06v5u2OxTWBWQbXmUJeVkRfgpDuCu6HfchrTjN5ybb8npplxg0wQWmw1EcDLdZTUvcByR28ApVUU6w';

const editorConfig = {
    toolbar: {
        items: [
            'undo', 'redo', '|', 'showBlocks', '|', 'heading', '|',
            'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
            'bold', 'italic', 'underline', '|',
            'link', 'insertImage', 'insertTable', 'blockQuote', 'codeBlock', '|',
            'alignment', '|',
            'bulletedList', 'numberedList', 'todoList', 'outdent', 'indent'
        ],
        shouldNotGroupWhenFull: false
    },
    plugins: [
        Alignment, Autoformat, AutoImage, AutoLink, Autosave, BalloonToolbar,
        Base64UploadAdapter, BlockQuote, Bold, Bookmark, Code, CodeBlock, Emoji,
        Essentials, FindAndReplace, FontBackgroundColor, FontColor, FontFamily,
        FontSize, Fullscreen, GeneralHtmlSupport, Heading, HorizontalLine,
        HtmlComment, HtmlEmbed, ImageBlock, ImageCaption, ImageEditing,
        ImageInline, ImageInsert, ImageInsertViaUrl, ImageResize, ImageStyle,
        ImageTextAlternative, ImageToolbar, ImageUpload, ImageUtils, Indent,
        IndentBlock, Italic, Link, List, ListProperties, Markdown,
        MediaEmbed, Mention, Minimap, PageBreak, Paragraph,
        PasteFromMarkdownExperimental, PasteFromOffice, RemoveFormat, ShowBlocks,
        SpecialCharacters, SpecialCharactersArrows, SpecialCharactersCurrency,
        SpecialCharactersEssentials, SpecialCharactersLatin,
        SpecialCharactersMathematical, SpecialCharactersText, Strikethrough,
        Subscript, Superscript, Table, TableCaption, TableCellProperties,
        TableColumnResize, TableProperties, TableToolbar, TextPartLanguage,
        TextTransformation, Title, TodoList, Underline, WordCount
    ],
    balloonToolbar: ['bold', 'italic', '|', 'link', 'insertImage', '|', 'bulletedList', 'numberedList'],
    fontFamily: { supportAllValues: true },
    fontSize: {
        options: [10, 12, 14, 'default', 18, 20, 22],
        supportAllValues: true
    },
    fullscreen: {
        onEnterCallback: container =>
            container.classList.add(
                'editor-container',
                'editor-container_document-editor',
                'editor-container_include-minimap',
                'editor-container_include-word-count',
                'editor-container_include-fullscreen',
                'main-container'
            )
    },
    heading: {
        options: [
            { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' },
            { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' },
            { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' },
            { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' },
            { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' },
            { model: 'heading5', view: 'h5', title: 'Heading 5', class: 'ck-heading_heading5' },
            { model: 'heading6', view: 'h6', title: 'Heading 6', class: 'ck-heading_heading6' }
        ]
    },
    htmlSupport: {
        allow: [{ name: /^.*$/, styles: true, attributes: true, classes: true }]
    },
    image: {
        toolbar: [
            'toggleImageCaption',
            'imageTextAlternative',
            '|',
            'imageStyle:inline',
            'imageStyle:wrapText',
            'imageStyle:breakText',
            '|',
            'resizeImage'
        ]
    },
    initialData: '<h2>Congratulations on setting up CKEditor 5! 🎉</h2>\n<p>...</p>', // abreviado
    language: 'es',
    licenseKey: LICENSE_KEY,
    link: {
        addTargetToExternalLinks: true,
        defaultProtocol: 'https://',
        decorators: {
            toggleDownloadable: {
                mode: 'manual',
                label: 'Downloadable',
                attributes: { download: 'file' }
            }
        }
    },
    list: {
        properties: { styles: true, startIndex: true, reversed: true }
    },
    mention: {
        feeds: [{ marker: '@', feed: [] }]
    },
    minimap: {
        container: document.querySelector('#editor-minimap'),
        extraClasses: 'editor-container_include-minimap ck-minimap__iframe-content'
    },
    placeholder: 'Type or paste your content here!',
    table: {
        contentToolbar: [
            'tableColumn',
            'tableRow',
            'mergeTableCells',
            'tableProperties',
            'tableCellProperties'
        ]
    }
};

/* -----------------------------------------------------------------
   3️⃣  CREAR EL EDITOR y HOOKS de comunicación
   ----------------------------------------------------------------- */
DecoupledEditor
    .create(document.querySelector('#editor'), editorConfig)
    .then(editor => {
        /* -----------------------------------------------------------------
           a)  GUARDAR EL editor en una variable global para depuración
           ----------------------------------------------------------------- */
        window.editorInstance = editor;                 // <-- disponible desde consola

        /* -----------------------------------------------------------------
           b)  RENDER UI del DecoupledEditor (toolbar, menubar, word‑count)
           ----------------------------------------------------------------- */
        const wordCount = editor.plugins.get('WordCount');
        document.querySelector('#editor-word-count').appendChild(wordCount.wordCountContainer);
        document.querySelector('#editor-toolbar').appendChild(editor.ui.view.toolbar.element);
        document.querySelector('#editor-menu-bar').appendChild(editor.ui.view.menuBarView.element);

        /* -----------------------------------------------------------------
           c)  NOTIFICAR al *padre* que el iframe está listo
           ----------------------------------------------------------------- */
        // Si tu página padre está en el mismo dominio puedes usar '*',
        // pero es más seguro especificar el origen exacto:
        const PARENT_ORIGIN = 'https://gestordecursos.pegui.edu.co';
        window.parent.postMessage({ type: 'ready' }, PARENT_ORIGIN);

        /* -----------------------------------------------------------------
           d)  ESCUCHAR LOS MENSAJES QUE ENVIARÁ EL PADRE
           ----------------------------------------------------------------- */
        window.addEventListener('message', event => {
            // Seguridad: aceptar sólo del dominio del padre
            if (event.origin !== PARENT_ORIGIN) return;

            const msg = event.data;
            if (!msg || typeof msg !== 'object') return;

            /* -------------------------------------------------------------
               1)  Obtener el contenido del editor (solicitud del padre)
               ------------------------------------------------------------- */
            if (msg.type === 'getContent') {
                const html = editor.getData();       // <-- CKEditor 5 devuelve HTML
                event.source.postMessage({ type: 'content', payload: html }, event.origin);
                return;
            }

            /* -------------------------------------------------------------
               2)  Insertar HTML recibido (solicitud "insertHTML")
               ------------------------------------------------------------- */
            if (msg.type === 'insertHTML') {
                const htmlToInsert = msg.payload;   // <-- string con el HTML que queremos insertar
                editor.model.change(writer => {
                    // Convertir la cadena HTML a un fragmento de modelo CKEditor
                    const viewFragment = editor.data.processor.toView(htmlToInsert);
                    const modelFragment = editor.data.toModel(viewFragment);
                    // Insertar en la posición del cursor o al final si no hay selección
                    editor.model.insertContent(modelFragment, editor.model.document.selection);
                });
                return;
            }
        });

        /* -----------------------------------------------------------------
           e)  Si deseas, puedes exponer funciones simples para depurar:
           ----------------------------------------------------------------- */
        window.getEditorContent = () => editor.getData();
        window.insertHTMLIntoEditor = html => {
            editor.model.change(writer => {
                const viewFragment = editor.data.processor.toView(html);
                const modelFragment = editor.data.toModel(viewFragment);
                editor.model.insertContent(modelFragment, editor.model.document.selection);
            });
        };

        /* -----------------------------------------------------------------
           f)  No es necesario devolver nada más; el resto del código de tu
              editor (p.ej. autosave) sigue funcionando como antes.
           ----------------------------------------------------------------- */
        console.log('✅ Editor CKEditor 5 listo y con postMessage habilitado');
    })
    .catch(error => {
        console.error('❌ Error al iniciar CKEditor 5:', error);
    });

