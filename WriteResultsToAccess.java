import java.io.FileNotFoundException;
import java.io.FileReader;
import java.sql.*;
import java.text.DateFormat;
import java.text.ParseException;
import java.text.SimpleDateFormat;
import java.util.Scanner;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class WriteResultsToAccess {

    static Scanner in = new Scanner(System.in);
    static Connection connection = null;
    static int currentSeason = 16;
    static String seasonType = "HS";
    static String filePath = "jdbc:ucanaccess://C:\\Users\\amain\\Documents\\Lobo Tennis.accdb";

    public static void main(String[] args) {

        try {
            Class.forName("net.ucanaccess.jdbc.UcanaccessDriver");// Loading Driver
            connection = DriverManager
                    .getConnection(filePath);// Establishing
                                                                                                       // Connection
            System.out.println("Connected Successfully");
            System.out.println("The current season is " + currentSeason + " " + seasonType + "\n");
            menu();

        } catch (Exception e) {
            System.out.println("Error in connection.");
            e.printStackTrace();

        } finally {

            // Step 3: Closing database connection
            try {
                if (null != connection) {
                    // and then finally close connection
                    connection.close();
                    System.out.println("Connection Closed\n");
                }
            } catch (SQLException sqlex) {
                sqlex.printStackTrace();
            }
        }

    }

    public static void menu() {
        int selection = 0;
        while (selection < 4) {
            boolean loop;

            do {
                try {
                    System.out.println(
                            "What would you like to do? \n1) Enter Fall Results\n2) Create Player\n3) Create Season\n4) Exit");
                    selection = in.nextInt();
                    in.nextLine();
                    loop = false;
                } catch (Exception e) {
                    System.out.println("Please make a valid selection");
                    in.nextLine();
                    loop = true;
                }
            } while (loop);

            switch (selection) {
                case 1 -> createFallResults();
                case 2 -> createPlayer();
                case 3 -> createSeason();
                default -> {
                }
            }
        }
    }

    public static void createFallResults() {
        try {
            Scanner file = new Scanner(new FileReader("match.txt"));

            int eventID = -1;

            // create new event
            if (file.hasNextLine()) {
                System.out.println("Are you sure you would like to create the following match? (y/n)");
                String data = file.nextLine();
                System.out.println(data);
                String confirm = in.nextLine();
                if (confirm.equals("y")) {
                    eventID = createEvent(data);
                }
            }

            // handle match results
            String type = null;
            while (file.hasNextLine() && eventID > -1) {
                String data = file.nextLine();
                data = data.trim();

                if (data.equals("Boys Doubles")) {
                    type = "B";
                    continue;
                }

                if (data.equals("Girls Doubles")) {
                    type = "G";
                    continue;
                }

                if (data.equals("Mixed Doubles")) {
                    type = "M";
                    continue;
                }

                if (data.equals("Boys Singles")) {
                    type = "S";
                    continue;
                }

                if (data.equals("") || data.equals(" ") || data.equals("Girls Singles") || type == null)
                    continue;

                // determine if doubles results are coming
                if (type != null) {
                    createMatchResult(data, type, eventID);
                }

            }

            file.close();
        } catch (FileNotFoundException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }

    }

    private static void createMatchResult(String d, String type, int event) {
        String[] data = d.split(" ");

        if (!(data[data.length - 1].equals("DNP"))) {

            int line = Integer.parseInt(data[0].substring(0, data[0].length() - 1));

            int id = -1;
            int player1 = -1;
            int player2 = -1;
            if (type.equals("S")) {
                id = nextID("match_singles");
                player1 = getPlayerID(data[1], data[2]);
            } else {
                id = nextID("match_doubles");
                String[] slash = data[2].split("\\/");
                player1 = getPlayerID(data[1], slash[0]);
                player2 = getPlayerID(slash[1], data[3]);
            }

            // figure out score
            // score var matches database schema from set1_lobo to set3_tb
            int[] score = { -1, -1, -1, -1, -1, -1, -1, -1, -1 };
            Pattern regex = Pattern.compile("[0-9]-[0-9]");
            for (String s : data) {
                Matcher m = regex.matcher(s);
                if (m.find()) {
                    String[] split = s.split("-");
                    // first set
                    if (score[0] == -1) {
                        score[0] = Integer.parseInt(split[0]);

                        if (split[1].indexOf('(') == -1) {
                            score[1] = Integer.parseInt(split[1]);
                        } else {
                            score[1] = Integer.parseInt(split[1].substring(0, split[1].indexOf('(')));
                            score[2] = Integer
                                    .parseInt(split[1].substring(split[1].indexOf('(') + 1, split[1].indexOf(')')));
                        }

                    } else if (score[3] == -1) { // second set
                        score[3] = Integer.parseInt(split[0]);
                        if (split[1].indexOf('(') == -1) {
                            score[4] = Integer.parseInt(split[1]);
                        } else {
                            score[4] = Integer.parseInt(split[1].substring(0, split[1].indexOf('(')));
                            score[5] = Integer
                                    .parseInt(split[1].substring(split[1].indexOf('(') + 1, split[1].indexOf(')')));
                        }
                    } else if (score[6] == -1) { // third set
                        // check if only tb score given
                        if (split[1].indexOf('(') == -1 && Integer.parseInt(split[0]) < 2
                                && Integer.parseInt(split[1]) < 2) {
                            if (Integer.parseInt(split[0]) > Integer.parseInt(split[1])) {
                                score[6] = 1;
                                score[7] = 0;
                                score[8] = Integer.parseInt(split[1]);
                            } else {
                                score[6] = 0;
                                score[7] = 1;
                                score[8] = Integer.parseInt(split[0]);
                            }
                        } else { // full third score
                            score[6] = Integer.parseInt(split[0]);
                            if (split[1].indexOf('(') == -1) {
                                score[7] = Integer.parseInt(split[1]);
                            } else {
                                score[7] = Integer.parseInt(split[1].substring(0, split[1].indexOf('(')));
                                score[8] = Integer
                                        .parseInt(split[1].substring(split[1].indexOf('(') + 1, split[1].indexOf(')')));
                            }
                        }
                    }
                }
            }

            // figure out who won
            int winner = 0;
            String result = "DNF";
            if (!(data[data.length - 1].equals(result))) {
                winner += (score[0] > score[1]) ? 1 : -1;
                if (score[3] != -1)
                    winner += (score[3] > score[4]) ? 1 : -1;
                if (score[6] != -1)
                    winner += (score[6] > score[7]) ? 1 : -1;

                if (winner > 0)
                    result = "W";
                else if (winner < 0)
                    result = "L";
            }

            // write to correct table
            if (type.equals("S")) {
                try {
                    String sql = "INSERT INTO match_singles(id,event,line,player,result,set1_lobo,set1_opp,set1_tb,set2_lobo,set2_opp,set2_tb,set3_lobo,set3_opp,set3_tb) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)";
                    PreparedStatement statement = connection.prepareStatement(sql);
                    statement.setInt(1, id);
                    statement.setInt(2, event);
                    statement.setInt(3, line);
                    statement.setInt(4, player1);
                    statement.setString(5, result);
                    statement.setInt(6, score[0]);
                    statement.setInt(7, score[1]);
                    if (score[2] > -1)
                        statement.setInt(8, score[2]);
                    else
                        statement.setNull(8, Types.INTEGER);
                    if (score[3] > -1)
                        statement.setInt(9, score[3]);
                    else
                        statement.setNull(9, Types.INTEGER);
                    if (score[4] > -1)
                        statement.setInt(10, score[4]);
                    else
                        statement.setNull(10, Types.INTEGER);
                    if (score[5] > -1)
                        statement.setInt(11, score[5]);
                    else
                        statement.setNull(11, Types.INTEGER);
                    if (score[6] > -1)
                        statement.setInt(12, score[6]);
                    else
                        statement.setNull(12, Types.INTEGER);
                    if (score[7] > -1)
                        statement.setInt(13, score[7]);
                    else
                        statement.setNull(13, Types.INTEGER);
                    if (score[8] > -1)
                        statement.setInt(14, score[8]);
                    else
                        statement.setNull(14, Types.INTEGER);

                    int row = statement.executeUpdate();

                    if (row > 0) {
                        System.out.printf("SUCCESS: %d %d %d %s %s\n", id, event, line, player1, result);
                    } else {
                        System.out.printf("FAILED: %d %d %d %s %s\n", id, event, line, player1, result);
                    }

                } catch (SQLException e) {
                    System.out.printf("FAILED: %d %d %d %s %s\n", id, event, line, player1, result);
                }
            } else {
                try {
                    String sql = "INSERT INTO match_doubles(id,event,line,type,player1,player2,result,set1_lobo,set1_opp,set1_tb,set2_lobo,set2_opp,set2_tb,set3_lobo,set3_opp,set3_tb) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)";
                    PreparedStatement statement = connection.prepareStatement(sql);
                    statement.setInt(1, id);
                    statement.setInt(2, event);
                    statement.setInt(3, line);
                    statement.setString(4, type);
                    statement.setInt(5, player1);
                    statement.setInt(6, player2);
                    statement.setString(7, result);
                    statement.setInt(8, score[0]);
                    statement.setInt(9, score[1]);
                    if (score[2] > -1)
                        statement.setInt(10, score[2]);
                    else
                        statement.setNull(10, Types.INTEGER);
                    if (score[3] > -1)
                        statement.setInt(11, score[3]);
                    else
                        statement.setNull(11, Types.INTEGER);
                    if (score[4] > -1)
                        statement.setInt(12, score[4]);
                    else
                        statement.setNull(12, Types.INTEGER);
                    if (score[5] > -1)
                        statement.setInt(13, score[5]);
                    else
                        statement.setNull(13, Types.INTEGER);
                    if (score[6] > -1)
                        statement.setInt(14, score[6]);
                    else
                        statement.setNull(14, Types.INTEGER);
                    if (score[7] > -1)
                        statement.setInt(15, score[7]);
                    else
                        statement.setNull(15, Types.INTEGER);
                    if (score[8] > -1)
                        statement.setInt(16, score[8]);
                    else
                        statement.setNull(16, Types.INTEGER);

                    int row = statement.executeUpdate();

                    if (row > 0) {
                        System.out.printf("SUCCESS: %d %d %d %s %d %d %s\n", id, event, line, type, player1, player2,
                                result);
                    } else {
                        System.out.printf("FAILED: %d %d %d %s %d %d %s\n", id, event, line, type, player1, player2,
                                result);
                    }

                } catch (SQLException e) {
                    System.out.printf("FAILED: %d %d %d %s %d %d %s\n", id, event, line, type, player1, player2,
                            result);
                }
            }
        }

    }

    private static int createEvent(String line) {
        String[] data = line.split(" ");
        String date = data[0];
        DateFormat df = new SimpleDateFormat("MM/dd/yy");
        java.util.Date jDate = null;
        try {
            jDate = df.parse(date);
        } catch (ParseException e1) {
            // TODO Auto-generated catch block
            e1.printStackTrace();
        }
        java.sql.Date sDate = new java.sql.Date(jDate.getTime());

        String type = "JV";
        String location = "Home";
        String opponent = data[3];

        if (data[1].equals("Varsity"))
            type = "V";

        if (data[1].equals("MSA"))
            type = "A";

        if (data[1].equals("MSB"))
            type = "B";

        if (data[2].equals("@")) {
            System.out.println("Where was this match played?");
            location = in.nextLine();
        }

        // if opponent's name is more than 1 word
        int i = 4;
        while (i != data.length - 1) {
            opponent = opponent.concat(" " + data[i]);
            i++;
        }

        // determine match score
        String[] score = data[data.length - 1].split("-");

        int win = 0;
        if (score[0].charAt(0) == 'W')
            win = 1;
        // remove W/L/T char
        score[0] = score[0].substring(1);
        int loboScore = Integer.parseInt(score[0]);
        int oppScore = Integer.parseInt(score[1]);

        int id = nextID("event");

        int district = 0;
        String[] distOpps = { "Tyler Legacy", "Forney", "North Forney", "Rockwall", "Rockwall-Heath", "Royse City" };
        if (seasonType == "HS") {
            for (String team : distOpps) {
                if (opponent.equals(team))
                    district = 1;
            }
        }

        System.out.println("Are you sure you want to create the following match? (y/n)");
        System.out.println("ID\tSeason\tOpponent\tDate\tLocation\tUs\tThem\tWin?\tType\tDistrict?");
        System.out.println(
                "-------------------------------------------------------------------------------------------------");
        System.out.printf("%d\t%d\t%s\t\t%s\t%s\t\t%d\t%d\t%d\t%s\t%d\n", id, currentSeason, opponent, date, location,
                loboScore, oppScore, win, type, district);

        String confirm = in.next();
        if (confirm.equals("y")) {
            try {
                String sql = "INSERT INTO event(id,season,opponent,match_date,location,score_lobo,score_opp,win,type,district) VALUES(?,?,?,?,?,?,?,?,?,?)";
                PreparedStatement statement = connection.prepareStatement(sql);
                statement.setInt(1, id);
                statement.setInt(2, currentSeason);
                statement.setString(3, opponent);
                statement.setDate(4, sDate);
                statement.setString(5, location);
                statement.setInt(6, loboScore);
                statement.setInt(7, oppScore);
                statement.setInt(8, win);
                statement.setString(9, type);
                statement.setInt(10, district);

                int row = statement.executeUpdate();

                if (row > 0) {
                    System.out.println("Match created successfully.");
                    return id;
                } else {
                    System.out.println("Insertion failed.");
                    return -1;
                }

            } catch (SQLException e) {
                System.out.println("Insertion failed.");
                e.printStackTrace();
                return -1;
            }
        }

        return -1;
    }

    public static void createSeason() {
        int id = nextID("season");
        System.out.println("Spring/Fall: ");
        String season = in.nextLine();
        System.out.println("Year: ");
        int year = Integer.parseInt(in.nextLine());
        System.out.println("HS/MS: ");
        String type = in.nextLine();

        int maxGradYear = 0;
        int minGradYear = 0;
        if (type.equals("HS")) {
            maxGradYear = year + 4;
            minGradYear = year + 1;
        } else {
            maxGradYear = year + 7;
            minGradYear = year + 5;
        }

        System.out.println(
                "Are you sure you want to create this season? (y/n)\n" + id + " " + type + " " + season + " " + year);
        String result = in.nextLine();
        if (result.equals("y")) {
            try {
                String sql = "INSERT INTO SEASON(ID,season,yr,type, max_grad_year, min_grad_year) VALUES(?,?,?,?,?,?)";
                PreparedStatement statement = connection.prepareStatement(sql);
                statement.setInt(1, id);
                statement.setString(2, season);
                statement.setInt(3, year);
                statement.setString(4, type);
                statement.setInt(5, maxGradYear);
                statement.setInt(6, minGradYear);

                int row = statement.executeUpdate();

                if (row > 0) {
                    System.out.println("A row has been inserted successfully.");
                } else {
                    System.out.println("Insertion failed.");
                }

            } catch (SQLException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }

        System.out.println("Set the new season as the current one? (y/n)\n");
        result = in.nextLine();
        if (result.equals("y")) {
            currentSeason = id;
            seasonType = type;
        }

    }

    public static void createPlayer() {
        int id = nextID("player");
        System.out.println("First Name: ");
        String first = in.nextLine();
        System.out.println("Last Name: ");
        String last = in.nextLine();
        System.out.println("M/F: ");
        String gender = in.nextLine();
        System.out.println("Grad Year: ");
        int gradYear = Integer.parseInt(in.nextLine());

        System.out.println("Are you sure you want to create this student? (y/n)\n" + id + " " + first + " " + last + " "
                + gender + " " + gradYear);
        String result = in.nextLine();
        if (result.equals("y")) {
            try {
                String sql = "INSERT INTO PLAYER(id,first_name,last_name,gender,grad_year,dropped) VALUES(?,?,?,?,?,?)";
                PreparedStatement statement = connection.prepareStatement(sql);
                statement.setInt(1, id);
                statement.setString(2, first);
                statement.setString(3, last);
                statement.setString(4, gender);
                statement.setInt(5, gradYear);
                statement.setInt(6, 0);

                int row = statement.executeUpdate();

                if (row > 0) {
                    System.out.println("A row has been inserted successfully.");
                } else {
                    System.out.println("Insertion failed.");
                }

            } catch (SQLException e) {
                // TODO Auto-generated catch block
                e.printStackTrace();
            }
        }
    }

    public static int nextID(String table) {
        try {
            Statement statement = connection.createStatement();
            ResultSet resultSet = statement.executeQuery("SELECT MAX(ID) FROM " + table);
            resultSet.next();
            return resultSet.getInt(1) + 1;
        } catch (SQLException e) {
            // TODO Auto-generated catch block
            e.printStackTrace();
            return -1;
        }
    }

    public static int getPlayerID(String first, String last) {
        try {
            String sql = "SELECT id FROM player WHERE first_name = ? AND last_name = ?";
            PreparedStatement statement = connection.prepareStatement(sql);
            statement.setString(1, first);
            statement.setString(2, last);
            ResultSet resultSet = statement.executeQuery();

            if (resultSet.next()) { // Check if there are results
                return resultSet.getInt(1);
            } else {
                System.out.println("No player found with name: " + first + " " + last);
                return -1;
            }
        } catch (SQLException e) {
            e.printStackTrace();
            return -1;
        }
    }

}