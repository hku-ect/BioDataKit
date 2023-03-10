import java.time.*;
import java.time.format.*;
import java.util.Calendar;

Table table;

// some colors for plotting lines
color orange = #ED8B0A;
color blue = #6392F5;
color green = #74D891;
color yellow = #DED35C;

int margin = 60; // don't draw near screen border

void setup() {
  size(800, 600);
  
  // if you want other data you need to change the filename here 
  // and download the latest data to the data folder of this sketch!
  table = loadTable("BioDataKit - enviro2.csv", "header");
  
  println(table.getRowCount() + " total rows in table");
}

void draw()
{
  background(32);
  // vars to determine min max values from the dataset
  float tempMin = 100.0;
  float tempMax = 0.0;
  float pressMin = 2000.0;
  float pressMax = 0.0;
  float humMin = 200.0;
  float humMax = 0.0;
  // Row counter 
  int rowCount = 0;

  // process all data to get min & max
  for (TableRow row : table.rows()) {

    float temp = row.getFloat("temperature");
    if (temp < tempMin ) tempMin = temp;
    if (temp > tempMax ) tempMax = temp;

    float press = row.getFloat("pressure");
    if (press < pressMin ) pressMin = press;
    if (press > pressMax ) pressMax = press;

    float hum = row.getFloat("humidy"); // yes typo, I know. It's in the Google sheet.
    if (hum < humMin ) humMin = hum;
    if (hum > humMax ) humMax = hum;
  }
  // draw the horizontal axis from the min max values
  horizAxis(tempMin, tempMax, pressMin, pressMax, humMin, humMax);

  for (TableRow row : table.rows()) {
    int time = row.getInt("timestamp");
    float temp = row.getFloat("temperature");
    float press = row.getFloat("pressure");
    float hum = row.getFloat("humidy");

    // this is used for horizontal scrolling throught the data. The mouseX position determines where 
    // we are in the CSV data (visibleRowPos)
    int visibleRowPos = int(map(mouseX, 0, width, 0, table.getRowCount()-width));
    if (rowCount > visibleRowPos)
    {
      if (rowCount % 144 == 0 ) // draw the date for every day (== 1440 minutes, every row is 10 minutes)
      {                         // it would be nicer to use timestamps for the x position
        pushMatrix();
        noFill();
        stroke(48);
        translate(rowCount-visibleRowPos, 0);
        line(0, 0, 0, height);
        rotate(PI/2);
        fill(127);
        stroke(0);
        textSize(12);
        text(timestampToDay(time), 5, 20);
        popMatrix();
      }

      // plot temperature
      float tpos = map(temp, tempMin, tempMax, height-margin, margin);    
      fill(orange);
      noStroke();
      circle(rowCount-visibleRowPos, tpos, 2);

      // plot pressure
      float ppos = map(press, pressMin, pressMax, height-margin, margin);    
      fill(green);
      noStroke();
      circle(rowCount-visibleRowPos, ppos, 2);

      // plot humidity
      float hpos = map(hum, humMin, humMax, height-margin, margin);    
      fill(blue);
      noStroke();
      circle(rowCount-visibleRowPos, hpos, 2);
    }
    rowCount++;
  }
}

String timestampToDay(int timeStamp)
{
  java.util.Date dateTime=new java.util.Date((long)timeStamp*1000);
  DateTimeFormatter customFormatter = DateTimeFormatter.ofPattern("dd-MM");
  LocalDateTime ldt = dateTime.toInstant().atOffset(ZoneOffset.UTC).toLocalDateTime();
  return ldt.format(customFormatter);//.dateTime.toString();
}

void horizAxis(float tmin, float tmax, float pmin, float pmax, float hmin, float hmax)
{
  // draw horizontal grid lines based on the min max values and add value indicators
  for (int i=int(tmin)+1;i<tmax;i+=1)
  {
    // we use the temperature to set vertical pos of the axis lines
    float tpos = map(i, tmin, tmax, height-margin, margin); 
    float ppos = map(tpos, height-margin, margin, pmin, pmax); 
    float hpos = map(tpos, height-margin, margin, hmin, hmax);
    textSize(12);
    fill(orange);
    text(i + "C", 1, int(tpos)-1); // temperature Celcius
    fill(green);
    text(int(ppos) + "Pa", 40, int(tpos)-1); // pressure Pascal hPa
    fill(blue);
    text(int(hpos) + "%", 110, int(tpos)-1); // humidity percentage
    stroke(48);
    line(0,tpos,width, tpos);
  }
}
