type FileParser = (content: string) => string;

const parseHtml: FileParser = (content) => content;

const parsePlainText: FileParser = (content) => `<pre>${content}</pre>`;

const parsersByExtension: Record<string, FileParser> = {
  '.html': parseHtml,
  '.htm': parseHtml,
  '.txt': parsePlainText,
};

export const supportedExtensions = Object.keys(parsersByExtension);

export const getFileExtension = (filename: string): string => {
  const dotIndex = filename.lastIndexOf('.');
  return dotIndex === -1 ? '' : filename.slice(dotIndex).toLowerCase();
};

export const parseFileToHtml = (filename: string, content: string): string => {
  const ext = getFileExtension(filename);
  const parser = parsersByExtension[ext];

  if (!parser) {
    const supported = supportedExtensions.join(', ');
    throw new Error(`Unsupported file type "${ext}". Supported: ${supported}`);
  }

  return parser(content);
};

export const getSupportedAcceptString = (): string =>
  supportedExtensions.join(',');
