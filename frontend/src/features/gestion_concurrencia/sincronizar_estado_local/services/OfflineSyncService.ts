export interface GitObject {
    type: 'attribute' | 'method' | 'class' | 'tree';
    data: any;
}

class OfflineSyncService {
    private store = new Map<string, GitObject>();
    private dbName = 'UmlGitDB';
    private storeName = 'objects';
    private db: IDBDatabase | null = null;

    constructor() {
        this.initDB();
    }

    private initDB() {
        const request = indexedDB.open(this.dbName, 1);
        request.onupgradeneeded = (e: IDBVersionChangeEvent) => {
            const db = (e.target as IDBOpenDBRequest).result;
            if (!db.objectStoreNames.contains(this.storeName)) {
                db.createObjectStore(this.storeName);
            }
        };
        request.onsuccess = (e) => {
            this.db = (e.target as IDBOpenDBRequest).result;
            this.loadAllFromDB();
        };
    }

    private loadAllFromDB() {
        if (!this.db) return;
        const transaction = this.db.transaction(this.storeName, 'readonly');
        const objectStore = transaction.objectStore(this.storeName);
        const request = objectStore.getAll();
        const keysRequest = objectStore.getAllKeys();

        request.onsuccess = () => {
            keysRequest.onsuccess = () => {
                const keys = keysRequest.result as string[];
                const values = request.result as GitObject[];
                for (let i = 0; i < keys.length; i++) {
                    this.store.set(keys[i], values[i]);
                }
            };
        };
    }

    // Cache un objeto, si ya existe no hace nada
    putObject(hash: string, obj: GitObject) {
        if (!this.store.has(hash)) {
            this.store.set(hash, obj);
            this.saveToDB(hash, obj);
        }
    }

    private saveToDB(hash: string, obj: GitObject) {
        if (!this.db) return;
        const transaction = this.db.transaction(this.storeName, 'readwrite');
        const store = transaction.objectStore(this.storeName);
        store.put(obj, hash);
    }

    getObject(hash: string): GitObject | undefined {
        return this.store.get(hash);
    }

    hasObject(hash: string): boolean {
        return this.store.has(hash);
    }

    // Devuelve todos los objetos (útil para debug o sincronización inicial)
    getAll(): Map<string, GitObject> {
        return this.store;
    }

    saveLocalDiagramState(state: any) {
        if (!this.db) {
            localStorage.setItem('diagrama_local', JSON.stringify(state));
            return;
        }
        const transaction = this.db.transaction(this.storeName, 'readwrite');
        const store = transaction.objectStore(this.storeName);
        store.put({ type: 'local_diagram', data: state }, 'DIAGRAMA_LOCAL');
    }

    async getLocalDiagramState(): Promise<any> {
        return new Promise((resolve) => {
            if (!this.db) {
                const stored = localStorage.getItem('diagrama_local');
                resolve(stored ? JSON.parse(stored) : null);
                return;
            }
            const transaction = this.db.transaction(this.storeName, 'readonly');
            const store = transaction.objectStore(this.storeName);
            const request = store.get('DIAGRAMA_LOCAL');
            request.onsuccess = () => {
                if (request.result && request.result.data) {
                    resolve(request.result.data);
                } else {
                    const stored = localStorage.getItem('diagrama_local');
                    resolve(stored ? JSON.parse(stored) : null);
                }
            };
            request.onerror = () => {
                const stored = localStorage.getItem('diagrama_local');
                resolve(stored ? JSON.parse(stored) : null);
            };
        });
    }
}

// Exportamos un singleton
export const offlineSyncService = new OfflineSyncService();
