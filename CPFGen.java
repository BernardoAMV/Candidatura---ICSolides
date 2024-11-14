// Classe em Java que gera uma base de dados fake com antecedentes criminais.

// Leitura obrigatória: https://www.calculadorafacil.com.br/computacao/validar-cpf

import java.io.FileWriter;
import java.io.IOException;
import java.util.ArrayList;
import java.util.LinkedList;
import java.util.List;
import java.util.Random;

public class CPFGen{
  static List<CPFRecord> hasRecords = new LinkedList<>(); // CPFs que garantidamente queremos que TENHAM antecedentes.
  static List<CPFRecord> noRecords = new LinkedList<>(); // CPFs que garantidamente queremos que NÃO TENHAM antecedentes.

  public static void main(String[] args) {
    generateValidCPFs(20);
}

public static void addToHasRecords(char[] cpfNum, Boolean antecedente) {
  if (antecedente)hasRecords.add(new CPFRecord(cpfNum, antecedente));

}

public static void addToNoRecords(char[] cpfNum, Boolean antecedente) {
  if (!antecedente)noRecords.add(new CPFRecord(cpfNum, antecedente));
}

public static void generateValidCPFs(int count) {
    List<CPFRecord> validCPFs = new ArrayList<>();
    Random random = new Random();

    while (validCPFs.size() < count) {
        StringBuilder cpfBuilder = new StringBuilder();
        for (int i = 0; i < 9; i++) {
            cpfBuilder.append(random.nextInt(10));
        }
        String cpfBase = cpfBuilder.toString();
        int firstCheckDigit = calculateCheckDigit(cpfBase, 10);
        int secondCheckDigit = calculateCheckDigit(cpfBase + firstCheckDigit, 11);
        String validCPF = cpfBase + firstCheckDigit + secondCheckDigit;
        boolean antecedente = random.nextBoolean();
        boolean isInHasRecords = false;
        boolean isInNoRecords = false;

        if(!hasRecords.isEmpty()) isInHasRecords = hasRecords.stream().anyMatch(record -> new String(record.getCPFNUM()).equals(validCPF));
        if(!noRecords.isEmpty())  isInNoRecords = noRecords.stream().anyMatch(record -> new String(record.getCPFNUM()).equals(validCPF));

        if (isInHasRecords) {
            CPFRecord newRecord = new CPFRecord(validCPF.toCharArray(), true);
            if(!isValidCPF(newRecord.getCPFNUM())) System.err.println("CPF Invalido sendo adicionado ao JSON.");
            validCPFs.add(newRecord);
        } else if (isInNoRecords) {
            CPFRecord newRecord = new CPFRecord(validCPF.toCharArray(), false);
            if(!isValidCPF(newRecord.getCPFNUM())) System.err.println("CPF Invalido sendo adicionado ao JSON.");
            validCPFs.add(newRecord);
        } else {
          CPFRecord newRecord = new CPFRecord(validCPF.toCharArray(), antecedente);
          if(!isValidCPF(newRecord.getCPFNUM())) System.err.println("CPF Invalido sendo adicionado ao JSON.");
          validCPFs.add(newRecord);
        }
    }
    try (FileWriter file = new FileWriter("banco_de_CPF.json")) {
        file.write("[\n");
        for (int i = 0; i < validCPFs.size(); i++) {
            CPFRecord record = validCPFs.get(i);
            file.write("{\"CPFNUM\": \"" + new String(record.getCPFNUM()) + "\", \"antecedente\": " + record.getAntecedente() + "}");
            if (i < validCPFs.size() - 1) {
                file.write(",\n");
            }
        }
        file.write("\n]");
        System.out.println("Valid CPFs have been written to valid_cpfs.json");
    } catch (IOException e) {
        e.printStackTrace();
    }
}

  public static boolean isValidCPF(char[] cpf) {
    if (cpf.length != 11) {
        return false; // CPF só tem 11 digitos. Se não, Formatar corretamente para ter apenas NUMEROS.
    }
    String cpfStr = new String(cpf);
    // Essa regex garante que só temos digitos.
    if (!cpfStr.matches("\\d{11}")) {
        return false;
    }
    int firstCheckDigit = calculateCheckDigit(cpfStr.substring(0, 9), 10);
    int secondCheckDigit = calculateCheckDigit(cpfStr.substring(0, 10), 11);
    return (firstCheckDigit == Character.getNumericValue(cpf[9]) &&
            secondCheckDigit == Character.getNumericValue(cpf[10]));
  }

  private static int calculateCheckDigit(String base, int weight) {
      int sum = 0;
      for (int i = 0; i < base.length(); i++) {
          sum += Character.getNumericValue(base.charAt(i)) * weight--;
      }
      int remainder = sum % 11;
      return remainder < 2 ? 0 : 11 - remainder;
  }

  // Recebe um CPF com pontos e traços e retira caracteres não-digitos. (111.222.333-04) -> (11122233304)
  public static char[] formatCPF(char[] cpf) {
    StringBuilder formattedCPF = new StringBuilder();

    for (char c : cpf) {
        if (Character.isDigit(c)) {
            formattedCPF.append(c);
        }
    }
  return formattedCPF.toString().toCharArray();
  }

}

record CPFRecord(char[] CPFNUM, Boolean antecedente) {
  public char[] getCPFNUM() {
    return CPFNUM;
  }

  public Boolean getAntecedente(){
    return antecedente;
  }
}