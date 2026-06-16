export const getFileExtension = (filename: string): string => {
  const dotIndex = filename.lastIndexOf('.');
  return dotIndex === -1 ? '' : filename.slice(dotIndex).toLowerCase();
};

export const getAcceptString = (extensions: string[]): string =>
  extensions.join(',');

export const getExtensionLabel = (extensions: string[]): string =>
  extensions.map((ext) => ext.replace(/^\./, '').toUpperCase()).join(', ');
