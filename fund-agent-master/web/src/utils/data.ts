export interface IDataSource {
  gender: string;
  'race/ethnicity': string;
  'parental level of education': string;
  lunch: string;
  'test preparation course': string;
  'math score': number;
  'reading score': number;
  'writing score': number;
}

export interface IField {
  fid: string;
  semanticType: string;
  analyticType: string;
}

export interface IDataSet {
  fields: IField[];
  dataSource: IDataSource[];
}

export const useFetch = async (): Promise<IDataSet> => {
  const response = await fetch('https://pub-2422ed4100b443659f588f2382cfc7b1.r2.dev/datasets/ds-students-service.json');
  if (!response.ok) {
    throw new Error('Failed to fetch data');
  }
  return response.json();
};