import { MongoClient, type Db } from 'mongodb';

declare global {
  var _mongoClientPromise: Promise<MongoClient> | undefined;
}

const DB_NAME = process.env.MONGODB_DB_NAME ?? 'ai-reader';

const getClientPromise = (): Promise<MongoClient> => {
  const uri = process.env.MONGODB_URI;
  if (!uri) {
    throw new Error('MONGODB_URI environment variable is not set');
  }

  if (process.env.NODE_ENV === 'development') {
    if (!global._mongoClientPromise) {
      global._mongoClientPromise = new MongoClient(uri).connect();
    }
    return global._mongoClientPromise;
  }

  return new MongoClient(uri).connect();
};

export const getDb = async (): Promise<Db> => {
  const client = await getClientPromise();
  return client.db(DB_NAME);
};
