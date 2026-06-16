export const supportedExtensions = [
  '.pdf', '.docx', '.pptx', '.html', '.htm', '.md', '.txt',
];

export const getFileExtension = (filename: string): string => {
  const dotIndex = filename.lastIndexOf('.');
  return dotIndex === -1 ? '' : filename.slice(dotIndex).toLowerCase();
};

export const getSupportedAcceptString = (): string =>
  supportedExtensions.join(',');
